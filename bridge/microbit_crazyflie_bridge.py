"""Persistent micro:bit-to-Crazyflie bridge with heartbeat auto-land."""

import argparse
from enum import Enum
import sys
import time

import cflib.crtp
import serial
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.motion_commander import MotionCommander
from cflib.utils import uri_helper
from serial.tools import list_ports


DEFAULT_URI = "radio://0/80/2M"
BAUD_RATE = 115_200
ARM_WINDOW_S = 10.0
HEARTBEAT_TIMEOUT_S = 2.0
TAKEOFF_HEIGHT_M = 0.4
TAKEOFF_VELOCITY_M_S = 0.2
MOVE_VELOCITY_M_S = 0.2
MIN_MOVE_DISTANCE_CM = 5
MAX_MOVE_DISTANCE_CM = 50
TURN_RATE_DEG_S = 72.0
MIN_TURN_ANGLE_DEG = 15
MAX_TURN_ANGLE_DEG = 180
VERTICAL_VELOCITY_M_S = 0.2
MIN_VERTICAL_STEP_CM = 5
MAX_VERTICAL_STEP_CM = 30
MIN_TARGET_HEIGHT_M = 0.25
MAX_TARGET_HEIGHT_M = 1.0
LEGACY_HOVER_TIME_S = 5.0


class FlightState(Enum):
    GROUND = "GROUND"
    ARMED = "ARMED"
    TAKING_OFF = "TAKING_OFF"
    AIRBORNE = "AIRBORNE"
    LANDING = "LANDING"
    FAULT = "FAULT"


def find_microbit_port() -> str | None:
    keywords = ("micro:bit", "microbit", "mbed", "cmsis-dap")
    matches = []

    for port in list_ports.comports():
        identity = " ".join(
            value or ""
            for value in (port.description, port.manufacturer, port.product)
        ).lower()
        if any(keyword in identity for keyword in keywords):
            matches.append(port.device)

    if len(matches) == 1:
        return matches[0]
    return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the persistent Pitsco Drone development bridge."
    )
    parser.add_argument(
        "--port",
        help="micro:bit serial port, for example COM16. Auto-detected when possible.",
    )
    parser.add_argument(
        "--uri",
        default=uri_helper.uri_from_env(default=DEFAULT_URI),
        help=f"Crazyflie URI (default: {DEFAULT_URI}).",
    )
    return parser.parse_args()


def send_line(connection: serial.Serial, response: str) -> None:
    connection.write(f"{response}\n".encode("utf-8"))
    connection.flush()
    print(f"PC -> micro:bit: {response}")


def flow_deck_is_present(scf: SyncCrazyflie) -> bool:
    try:
        value = scf.cf.param.get_value("deck.bcFlow2")
    except (KeyError, TypeError, ValueError):
        return False
    return str(value).strip().lower() in {"1", "true"}


class FlightSession:
    def __init__(self, scf: SyncCrazyflie, flow_ready: bool) -> None:
        self.scf = scf
        self.flow_ready = flow_ready
        self.state = FlightState.GROUND
        self.armed_until = 0.0
        self.last_heartbeat = 0.0
        self.target_height_m = 0.0
        self.commander: MotionCommander | None = None

    def status_response(self) -> str:
        if not self.flow_ready:
            return "NOT_READY:NO_FLOW2"
        if self.state == FlightState.FAULT:
            return "NOT_READY:FAULT"
        return "READY"

    def arm(self) -> str:
        if not self.flow_ready:
            return "NOT_READY:NO_FLOW2"
        if self.state != FlightState.GROUND:
            return f"ERROR:STATE:{self.state.value}"

        self.armed_until = time.monotonic() + ARM_WINDOW_S
        self.state = FlightState.ARMED
        print(f"Flight armed for {ARM_WINDOW_S:.0f} seconds.")
        return "ARMED"

    def disarm(self) -> str:
        if self.state == FlightState.ARMED:
            self.armed_until = 0.0
            self.state = FlightState.GROUND
            return "DISARMED"
        if self.state == FlightState.GROUND:
            return "DISARMED"
        return f"ERROR:STATE:{self.state.value}"

    def _authorization_is_valid(self) -> bool:
        return (
            self.state == FlightState.ARMED
            and time.monotonic() <= self.armed_until
        )

    def take_off(self) -> str:
        if not self._authorization_is_valid():
            self.armed_until = 0.0
            if self.state == FlightState.ARMED:
                self.state = FlightState.GROUND
            return "NOT_ARMED"

        # Consume authorization before starting the motors.
        self.armed_until = 0.0
        self.state = FlightState.TAKING_OFF
        self.commander = MotionCommander(
            self.scf,
            default_height=TAKEOFF_HEIGHT_M,
        )

        try:
            print(f"Taking off to {TAKEOFF_HEIGHT_M:.1f} m ...")
            self.commander.take_off(
                height=TAKEOFF_HEIGHT_M,
                velocity=TAKEOFF_VELOCITY_M_S,
            )
        except Exception:
            self.state = FlightState.FAULT
            self.cleanup()
            raise

        self.state = FlightState.AIRBORNE
        self.target_height_m = TAKEOFF_HEIGHT_M
        self.last_heartbeat = time.monotonic()
        print("Airborne and holding position.")
        return "AIRBORNE"

    def heartbeat(self) -> None:
        if self.state == FlightState.AIRBORNE:
            self.last_heartbeat = time.monotonic()

    def move(self, direction: str, distance_cm: int) -> str:
        if self.state != FlightState.AIRBORNE or self.commander is None:
            return f"ERROR:STATE:{self.state.value}"

        normalized_direction = direction.strip().upper()
        movement = {
            "FORWARD": self.commander.forward,
            "BACKWARD": self.commander.back,
            "LEFT": self.commander.left,
            "RIGHT": self.commander.right,
        }.get(normalized_direction)
        if movement is None:
            return "ERROR:DIRECTION"
        if not MIN_MOVE_DISTANCE_CM <= distance_cm <= MAX_MOVE_DISTANCE_CM:
            return "ERROR:DISTANCE"

        distance_m = distance_cm / 100.0
        print(
            f"Moving {normalized_direction.lower()} {distance_cm} cm "
            f"at {MOVE_VELOCITY_M_S:.1f} m/s ..."
        )

        # A bounded motion command is itself evidence of a live controller.
        # The MakeCode side pauses heartbeats while waiting for this reply.
        self.last_heartbeat = time.monotonic()
        try:
            movement(distance_m, velocity=MOVE_VELOCITY_M_S)
        except Exception:
            try:
                self.land(reason="movement error")
            finally:
                raise

        self.last_heartbeat = time.monotonic()
        print("Movement complete; holding position.")
        return "MOVED"

    def turn(self, direction: str, angle_degrees: int) -> str:
        if self.state != FlightState.AIRBORNE or self.commander is None:
            return f"ERROR:STATE:{self.state.value}"

        normalized_direction = direction.strip().upper()
        rotation = {
            "LEFT": self.commander.turn_left,
            "RIGHT": self.commander.turn_right,
        }.get(normalized_direction)
        if rotation is None:
            return "ERROR:DIRECTION"
        if not MIN_TURN_ANGLE_DEG <= angle_degrees <= MAX_TURN_ANGLE_DEG:
            return "ERROR:ANGLE"

        print(
            f"Turning {normalized_direction.lower()} {angle_degrees} degrees "
            f"at {TURN_RATE_DEG_S:.0f} deg/s ..."
        )
        self.last_heartbeat = time.monotonic()
        try:
            rotation(angle_degrees, rate=TURN_RATE_DEG_S)
        except Exception:
            try:
                self.land(reason="turn error")
            finally:
                raise

        self.last_heartbeat = time.monotonic()
        print("Turn complete; holding position.")
        return "TURNED"

    def change_altitude(self, direction: str, distance_cm: int) -> str:
        if self.state != FlightState.AIRBORNE or self.commander is None:
            return f"ERROR:STATE:{self.state.value}"

        normalized_direction = direction.strip().upper()
        vertical_motion = {
            "UP": self.commander.up,
            "DOWN": self.commander.down,
        }.get(normalized_direction)
        if vertical_motion is None:
            return "ERROR:DIRECTION"
        if not MIN_VERTICAL_STEP_CM <= distance_cm <= MAX_VERTICAL_STEP_CM:
            return "ERROR:DISTANCE"

        signed_distance_m = distance_cm / 100.0
        if normalized_direction == "DOWN":
            signed_distance_m = -signed_distance_m
        proposed_height_m = round(
            self.target_height_m + signed_distance_m,
            3,
        )
        if not MIN_TARGET_HEIGHT_M <= proposed_height_m <= MAX_TARGET_HEIGHT_M:
            return "ERROR:ALTITUDE_LIMIT"

        print(
            f"Moving {normalized_direction.lower()} {distance_cm} cm "
            f"toward {proposed_height_m:.2f} m ..."
        )
        self.last_heartbeat = time.monotonic()
        try:
            vertical_motion(
                distance_cm / 100.0,
                velocity=VERTICAL_VELOCITY_M_S,
            )
        except Exception:
            try:
                self.land(reason="altitude command error")
            finally:
                raise

        self.target_height_m = proposed_height_m
        self.last_heartbeat = time.monotonic()
        print("Altitude change complete; holding position.")
        return "ALTITUDE_CHANGED"

    def land(self, reason: str = "command") -> str:
        if self.state == FlightState.GROUND:
            self.target_height_m = 0.0
            return "LANDED"
        if self.commander is None:
            self.state = FlightState.GROUND
            self.target_height_m = 0.0
            return "LANDED"

        print(f"Landing ({reason}) ...")
        self.state = FlightState.LANDING

        try:
            self.commander.land()
        except Exception:
            self.state = FlightState.FAULT
            try:
                self.scf.cf.commander.send_stop_setpoint()
            except Exception:
                pass
            raise
        else:
            self.state = FlightState.GROUND
            print("Landed.")
            return "LANDED"
        finally:
            self.commander = None
            self.last_heartbeat = 0.0
            self.target_height_m = 0.0

    def check_timeouts(self) -> None:
        now = time.monotonic()

        if self.state == FlightState.ARMED and now > self.armed_until:
            self.armed_until = 0.0
            self.state = FlightState.GROUND
            print("Arm window expired.")

        if (
            self.state == FlightState.AIRBORNE
            and now - self.last_heartbeat > HEARTBEAT_TIMEOUT_S
        ):
            print(
                f"No heartbeat for {HEARTBEAT_TIMEOUT_S:.1f} seconds; "
                "initiating automatic landing."
            )
            self.land(reason="heartbeat timeout")

    def run_legacy_test_flight(self) -> str:
        response = self.take_off()
        if response != "AIRBORNE":
            return response

        print(f"Legacy test hover for {LEGACY_HOVER_TIME_S:.0f} seconds ...")
        time.sleep(LEGACY_HOVER_TIME_S)
        return self.land(reason="legacy test complete")

    def cleanup(self) -> None:
        self.armed_until = 0.0
        if self.commander is None:
            if self.state != FlightState.FAULT:
                self.state = FlightState.GROUND
                self.target_height_m = 0.0
            return

        try:
            self.land(reason="bridge cleanup")
        except Exception as error:
            print(f"Cleanup landing failed: {error}", file=sys.stderr)


def handle_command(
    connection: serial.Serial,
    flight: FlightSession,
    command: str,
) -> None:
    if command != "HEARTBEAT":
        print(f"micro:bit -> PC: {command}")

    try:
        if command == "STATUS":
            send_line(connection, flight.status_response())
        elif command == "FLIGHT_STATUS":
            send_line(connection, flight.state.value)
        elif command == "ARM":
            send_line(connection, flight.arm())
        elif command == "DISARM":
            send_line(connection, flight.disarm())
        elif command == "TAKEOFF":
            send_line(connection, flight.take_off())
        elif command == "LAND":
            send_line(connection, flight.land())
        elif command.startswith("MOVE:"):
            parts = command.split(":")
            if len(parts) != 3:
                send_line(connection, "ERROR:FORMAT")
            else:
                try:
                    distance_cm = int(parts[2])
                except ValueError:
                    send_line(connection, "ERROR:DISTANCE")
                else:
                    send_line(
                        connection,
                        flight.move(parts[1], distance_cm),
                    )
        elif command.startswith("TURN:"):
            parts = command.split(":")
            if len(parts) != 3:
                send_line(connection, "ERROR:FORMAT")
            else:
                try:
                    angle_degrees = int(parts[2])
                except ValueError:
                    send_line(connection, "ERROR:ANGLE")
                else:
                    send_line(
                        connection,
                        flight.turn(parts[1], angle_degrees),
                    )
        elif command.startswith("ALTITUDE:"):
            parts = command.split(":")
            if len(parts) != 3:
                send_line(connection, "ERROR:FORMAT")
            else:
                try:
                    distance_cm = int(parts[2])
                except ValueError:
                    send_line(connection, "ERROR:DISTANCE")
                else:
                    send_line(
                        connection,
                        flight.change_altitude(parts[1], distance_cm),
                    )
        elif command == "HEARTBEAT":
            flight.heartbeat()
        elif command == "TEST_FLIGHT":
            send_line(connection, flight.run_legacy_test_flight())
        else:
            send_line(connection, f"UNKNOWN:{command}")
    except Exception as error:
        print(f"Command {command} failed: {error}", file=sys.stderr)
        send_line(connection, "FLIGHT_ERROR")


def command_loop(connection: serial.Serial, flight: FlightSession) -> None:
    receive_buffer = bytearray()

    while True:
        # A serial timeout can return only part of a command. Accumulate bytes
        # and dispatch only newline-terminated records.
        chunk = connection.read(connection.in_waiting or 1)
        if chunk:
            receive_buffer.extend(chunk)

        while b"\n" in receive_buffer:
            raw_line, _, remainder = receive_buffer.partition(b"\n")
            receive_buffer = bytearray(remainder)

            command = raw_line.decode(
                "utf-8", errors="replace"
            ).strip().upper()
            if command:
                handle_command(connection, flight, command)

        flight.check_timeouts()


def main() -> int:
    args = parse_args()
    port = args.port or find_microbit_port()

    if port is None:
        print("Could not uniquely identify the micro:bit serial port.", file=sys.stderr)
        print("Specify the port explicitly with --port COMx.")
        return 2

    cflib.crtp.init_drivers()
    print(f"Opening micro:bit on {port} at {BAUD_RATE} baud ...")

    try:
        with serial.Serial(port, BAUD_RATE, timeout=0.1) as connection:
            time.sleep(1.0)
            connection.reset_input_buffer()

            print(f"Connecting to Crazyflie at {args.uri} ...")
            with SyncCrazyflie(
                args.uri,
                cf=Crazyflie(rw_cache="./cache"),
            ) as scf:
                print("Crazyflie connected. Waiting for parameters ...")
                scf.wait_for_params()

                flow_ready = flow_deck_is_present(scf)
                print(f"Flow Deck V2 detected: {'yes' if flow_ready else 'no'}")
                print(
                    "Commands: STATUS, FLIGHT_STATUS, ARM, DISARM, "
                    "TAKEOFF, LAND, MOVE, TURN, ALTITUDE, HEARTBEAT"
                )
                print("Press Ctrl+C to stop; an airborne drone will be landed.")

                flight = FlightSession(scf, flow_ready)
                try:
                    command_loop(connection, flight)
                finally:
                    flight.cleanup()

    except KeyboardInterrupt:
        print("\nPersistent bridge stopped.")
        return 0
    except serial.SerialException as error:
        print(f"Serial error: {error}", file=sys.stderr)
        return 1
    except Exception as error:
        print(f"Crazyflie connection error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

