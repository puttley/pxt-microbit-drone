/**
 * Guarded Crazyflie commands sent through the PC serial bridge.
 */
//% color=#006970 weight=90 icon="\uf1d8" block="Drone"
namespace drone {
    let armed = false
    let response = ""

    function sendCommand(command: string): string {
        serial.writeLine(command)
        response = serial.readUntil(serial.delimiters(Delimiters.NewLine))
        return response
    }

    /**
     * Configure USB serial communication with the PC bridge.
     */
    //% blockId=drone_initialize block="initialize drone link"
    //% weight=100
    export function initialize(): void {
        armed = false
        response = ""
        serial.redirectToUSB()
        serial.setBaudRate(BaudRate.BaudRate115200)
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
     * Open the bridge's short authorization window for one test flight.
     */
    //% blockId=drone_arm_test block="arm one test flight"
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
        return sendCommand("TEST_FLIGHT") == "LANDED"
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
