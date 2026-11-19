"""Unit tests for the persistent bridge state machine (no hardware required)."""

import unittest
from unittest.mock import patch

import microbit_crazyflie_bridge as bridge


class FakeCrazyflieCommander:
    def __init__(self) -> None:
        self.stop_count = 0

    def send_stop_setpoint(self) -> None:
        self.stop_count += 1


class FakeCrazyflie:
    def __init__(self) -> None:
        self.commander = FakeCrazyflieCommander()


class FakeSyncCrazyflie:
    def __init__(self) -> None:
        self.cf = FakeCrazyflie()


class FakeMotionCommander:
    instances = []

    def __init__(self, scf, default_height) -> None:
        self.scf = scf
        self.default_height = default_height
        self.takeoff_count = 0
        self.land_count = 0
        self.moves = []
        self.turns = []
        self.altitude_changes = []
        FakeMotionCommander.instances.append(self)

    def take_off(self, height, velocity) -> None:
        self.takeoff_count += 1

    def land(self) -> None:
        self.land_count += 1

    def forward(self, distance_m, velocity) -> None:
        self.moves.append(("FORWARD", distance_m, velocity))

    def back(self, distance_m, velocity) -> None:
        self.moves.append(("BACKWARD", distance_m, velocity))

    def left(self, distance_m, velocity) -> None:
        self.moves.append(("LEFT", distance_m, velocity))

    def right(self, distance_m, velocity) -> None:
        self.moves.append(("RIGHT", distance_m, velocity))

    def turn_left(self, angle_degrees, rate) -> None:
        self.turns.append(("LEFT", angle_degrees, rate))

    def turn_right(self, angle_degrees, rate) -> None:
        self.turns.append(("RIGHT", angle_degrees, rate))

    def up(self, distance_m, velocity) -> None:
        self.altitude_changes.append(("UP", distance_m, velocity))

    def down(self, distance_m, velocity) -> None:
        self.altitude_changes.append(("DOWN", distance_m, velocity))


class FlightSessionTests(unittest.TestCase):
    def setUp(self) -> None:
        FakeMotionCommander.instances.clear()
        self.scf = FakeSyncCrazyflie()
        self.motion_patch = patch.object(
            bridge,
            "MotionCommander",
            FakeMotionCommander,
        )
        self.motion_patch.start()

    def tearDown(self) -> None:
        self.motion_patch.stop()

    def test_takeoff_requires_arm(self) -> None:
        flight = bridge.FlightSession(self.scf, flow_ready=True)

        self.assertEqual("NOT_ARMED", flight.take_off())
        self.assertEqual(bridge.FlightState.GROUND, flight.state)

    def test_arm_takeoff_and_land(self) -> None:
        flight = bridge.FlightSession(self.scf, flow_ready=True)

        self.assertEqual("ARMED", flight.arm())
        self.assertEqual("AIRBORNE", flight.take_off())
        self.assertEqual(bridge.FlightState.AIRBORNE, flight.state)
        self.assertEqual("LANDED", flight.land())
        self.assertEqual(bridge.FlightState.GROUND, flight.state)

        commander = FakeMotionCommander.instances[0]
        self.assertEqual(1, commander.takeoff_count)
        self.assertEqual(1, commander.land_count)

    def test_arm_window_expires(self) -> None:
        flight = bridge.FlightSession(self.scf, flow_ready=True)

        self.assertEqual("ARMED", flight.arm())
        flight.armed_until = 0.0
        flight.check_timeouts()

        self.assertEqual(bridge.FlightState.GROUND, flight.state)
        self.assertEqual("NOT_ARMED", flight.take_off())

    def test_missing_heartbeat_lands(self) -> None:
        flight = bridge.FlightSession(self.scf, flow_ready=True)

        flight.arm()
        flight.take_off()
        flight.last_heartbeat = 0.0
        flight.check_timeouts()

        self.assertEqual(bridge.FlightState.GROUND, flight.state)
        self.assertEqual(1, FakeMotionCommander.instances[0].land_count)

    def test_cleanup_lands_airborne_drone(self) -> None:
        flight = bridge.FlightSession(self.scf, flow_ready=True)

        flight.arm()
        flight.take_off()
        flight.cleanup()

        self.assertEqual(bridge.FlightState.GROUND, flight.state)
        self.assertEqual(1, FakeMotionCommander.instances[0].land_count)

    def test_flow_deck_is_required(self) -> None:
        flight = bridge.FlightSession(self.scf, flow_ready=False)

        self.assertEqual("NOT_READY:NO_FLOW2", flight.status_response())
        self.assertEqual("NOT_READY:NO_FLOW2", flight.arm())

    def test_move_requires_airborne_state(self) -> None:
        flight = bridge.FlightSession(self.scf, flow_ready=True)

        self.assertEqual("ERROR:STATE:GROUND", flight.move("FORWARD", 20))

    def test_bounded_horizontal_moves(self) -> None:
        flight = bridge.FlightSession(self.scf, flow_ready=True)
        flight.arm()
        flight.take_off()

        for direction in ("FORWARD", "BACKWARD", "LEFT", "RIGHT"):
            with self.subTest(direction=direction):
                self.assertEqual("MOVED", flight.move(direction, 20))

        commander = FakeMotionCommander.instances[0]
        self.assertEqual(
            [
                ("FORWARD", 0.2, bridge.MOVE_VELOCITY_M_S),
                ("BACKWARD", 0.2, bridge.MOVE_VELOCITY_M_S),
                ("LEFT", 0.2, bridge.MOVE_VELOCITY_M_S),
                ("RIGHT", 0.2, bridge.MOVE_VELOCITY_M_S),
            ],
            commander.moves,
        )

    def test_move_rejects_invalid_direction_and_distance(self) -> None:
        flight = bridge.FlightSession(self.scf, flow_ready=True)
        flight.arm()
        flight.take_off()

        self.assertEqual("ERROR:DIRECTION", flight.move("UP", 20))
        self.assertEqual("ERROR:DISTANCE", flight.move("FORWARD", 4))
        self.assertEqual("ERROR:DISTANCE", flight.move("FORWARD", 51))

    def test_bounded_yaw_turns(self) -> None:
        flight = bridge.FlightSession(self.scf, flow_ready=True)
        flight.arm()
        flight.take_off()

        self.assertEqual("TURNED", flight.turn("LEFT", 45))
        self.assertEqual("TURNED", flight.turn("RIGHT", 45))
        self.assertEqual(
            [
                ("LEFT", 45, bridge.TURN_RATE_DEG_S),
                ("RIGHT", 45, bridge.TURN_RATE_DEG_S),
            ],
            FakeMotionCommander.instances[0].turns,
        )

    def test_turn_rejects_invalid_state_direction_and_angle(self) -> None:
        flight = bridge.FlightSession(self.scf, flow_ready=True)
        self.assertEqual("ERROR:STATE:GROUND", flight.turn("LEFT", 45))

        flight.arm()
        flight.take_off()
        self.assertEqual("ERROR:DIRECTION", flight.turn("UP", 45))
        self.assertEqual("ERROR:ANGLE", flight.turn("LEFT", 14))
        self.assertEqual("ERROR:ANGLE", flight.turn("LEFT", 181))

    def test_bounded_altitude_changes(self) -> None:
        flight = bridge.FlightSession(self.scf, flow_ready=True)
        flight.arm()
        flight.take_off()

        self.assertEqual("ALTITUDE_CHANGED", flight.change_altitude("UP", 10))
        self.assertEqual(0.5, flight.target_height_m)
        self.assertEqual("ALTITUDE_CHANGED", flight.change_altitude("DOWN", 10))
        self.assertEqual(0.4, flight.target_height_m)
        self.assertEqual(
            [
                ("UP", 0.1, bridge.VERTICAL_VELOCITY_M_S),
                ("DOWN", 0.1, bridge.VERTICAL_VELOCITY_M_S),
            ],
            FakeMotionCommander.instances[0].altitude_changes,
        )

    def test_altitude_rejects_invalid_values_and_accumulated_limits(self) -> None:
        flight = bridge.FlightSession(self.scf, flow_ready=True)
        self.assertEqual(
            "ERROR:STATE:GROUND",
            flight.change_altitude("UP", 10),
        )

        flight.arm()
        flight.take_off()
        self.assertEqual("ERROR:DIRECTION", flight.change_altitude("LEFT", 10))
        self.assertEqual("ERROR:DISTANCE", flight.change_altitude("UP", 4))
        self.assertEqual("ERROR:DISTANCE", flight.change_altitude("UP", 31))
        self.assertEqual(
            "ERROR:ALTITUDE_LIMIT",
            flight.change_altitude("DOWN", 20),
        )
        self.assertEqual("ALTITUDE_CHANGED", flight.change_altitude("UP", 30))
        self.assertEqual("ALTITUDE_CHANGED", flight.change_altitude("UP", 30))
        self.assertEqual(
            "ERROR:ALTITUDE_LIMIT",
            flight.change_altitude("UP", 5),
        )


if __name__ == "__main__":
    unittest.main()

