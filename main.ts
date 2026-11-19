/**
 * Guarded Crazyflie commands sent through the PC serial bridge.
 */
//% color=#006970 weight=90 icon="\uf1d8" block="Pitsco Drone"
namespace drone {
    const RESPONSE_POLL_MS = 10
    const RESPONSE_TIMEOUT_POLLS = 1500
    let armed = false
    let airborne = false
    let commandBusy = false
    let heartbeatStarted = false
    let response = ""

    function sendCommand(command: string): string {
        commandBusy = true
        serial.writeLine(command)

        // USB serial reads may return before the PC bridge has replied. Poll
        // for a complete line so the next command cannot consume this reply.
        response = ""
        for (let attempt = 0; attempt < RESPONSE_TIMEOUT_POLLS; attempt++) {
            response = serial.readUntil(serial.delimiters(Delimiters.NewLine))
            if (response.length > 0) {
                break
            }
            basic.pause(RESPONSE_POLL_MS)
        }

        commandBusy = false
        return response
    }

    function startHeartbeat(): void {
        if (heartbeatStarted) {
            return
        }

        heartbeatStarted = true
        control.inBackground(function () {
            while (true) {
                if (airborne && !commandBusy) {
                    serial.writeLine("HEARTBEAT")
                }
                basic.pause(500)
            }
        })
    }

    /**
     * Configure USB serial communication with the PC bridge.
     */
    //% blockId=drone_initialize block="initialize drone link"
    //% weight=100
    export function initialize(): void {
        armed = false
        airborne = false
        commandBusy = false
        response = ""
        serial.redirectToUSB()
        serial.setBaudRate(BaudRate.BaudRate115200)
        serial.readString()
        startHeartbeat()
    }

    /**
     * Check that the Crazyflie and Flow Deck are ready.
     */
    //% blockId=drone_is_ready block="drone is ready"
    //% weight=90
    export function isReady(): boolean {
        return sendCommand("STATUS") == "READY"
    }

    /**
     * Open the bridge's short authorization window for one flight.
     */
    //% blockId=drone_arm_test block="arm drone"
    //% weight=80
    export function armTestFlight(): boolean {
        armed = sendCommand("ARM") == "ARMED"
        return armed
    }

    /**
     * Cancel the current test-flight authorization.
     */
    //% blockId=drone_disarm block="disarm drone"
    //% weight=70
    export function disarm(): boolean {
        armed = false
        return sendCommand("DISARM") == "DISARMED"
    }

    /**
     * Take off to the validated height of 40 cm and hold position.
     */
    //% blockId=drone_take_off block="take off"
    //% weight=65
    export function takeOff(): boolean {
        if (!armed) {
            return false
        }

        // Consume local authorization before sending the flight command.
        armed = false
        airborne = sendCommand("TAKEOFF") == "AIRBORNE"
        return airborne
    }

    /**
     * Perform a controlled landing.
     */
    //% blockId=drone_land block="land"
    //% weight=64
    export function land(): boolean {
        let landed = sendCommand("LAND") == "LANDED"
        if (landed) {
            airborne = false
            armed = false
        }
        return landed
    }

    /**
     * Ask the bridge whether the drone is currently airborne.
     */
    //% blockId=drone_is_flying block="drone is flying"
    //% weight=63
    export function isFlying(): boolean {
        airborne = sendCommand("FLIGHT_STATUS") == "AIRBORNE"
        return airborne
    }

    /**
     * Return the bridge flight state as text.
     */
    //% blockId=drone_flight_status block="flight status"
    //% weight=12 advanced=true
    export function flightStatus(): string {
        return sendCommand("FLIGHT_STATUS")
    }

    /**
     * Run one 0.4 m takeoff, five-second hover, and automatic landing.
     */
    //% blockId=drone_run_test block="run armed test flight"
    //% weight=60
    export function runTestFlight(): boolean {
        if (!armed) {
            return false
        }

        // Consume the local authorization before sending the flight command.
        armed = false
        let landed = sendCommand("TEST_FLIGHT") == "LANDED"
        airborne = false
        return landed
    }

    /**
     * Return the most recent response received from the PC bridge.
     */
    //% blockId=drone_last_response block="last drone response"
    //% weight=10 advanced=true
    export function lastResponse(): string {
        return response
    }
}
