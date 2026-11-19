# microbit-drone

Experimental Microsoft MakeCode blocks for guarded control of a Crazyflie 2.1
through a USB-connected micro:bit and a Python PC bridge.

## Current blocks

- `initialize drone link`
- `drone is ready`
- `arm drone`
- `disarm drone`
- `take off`
- `land`
- `drone is flying`
- `move [direction] [distance] cm`
- `turn [direction] [angle] degrees`
- `change altitude [up/down] [distance] cm`
- `flight status` (advanced)
- `run armed test flight`
- `last drone response` (advanced)

## Safety model

The initial flight command is deliberately constrained. The Python bridge only
accepts `TEST_FLIGHT` during a 10-second authorization window opened by `ARM`.
Authorization is consumed before takeoff. The aircraft takes off to 0.4 m,
hovers for five seconds, and lands automatically.

The persistent-flight development bridge also accepts separate takeoff and
land commands. While airborne, the extension sends a heartbeat every 500 ms.
If the Python bridge receives no heartbeat for two seconds, it commands a
controlled landing. This is a development safety layer and does not replace
the Crazyflie firmware supervisor.

Horizontal movement is accepted only while the bridge is in the `AIRBORNE`
state. Distance is limited to 5-50 cm and speed is fixed at 0.2 m/s. Each
bounded movement refreshes the bridge heartbeat timer when it completes.
Yaw turns are limited to 15-180 degrees and use a fixed rate of 72 degrees per
second. Turns are accepted only while airborne and also refresh the heartbeat
timer on completion.
Vertical steps are limited to 5-30 cm. The bridge tracks commanded height and
rejects a step that would move the target below 0.25 m or above 1.0 m.

## Architecture

`MakeCode blocks -> micro:bit USB serial -> Python bridge -> Crazyradio -> Crazyflie`

This version is PC-tethered and does not communicate directly from the
micro:bit to the Crazyflie radio.

## Add to MakeCode

1. Open the micro:bit MakeCode editor.
2. Select **Extensions**.
3. Paste this repository URL into the search box:
   `https://github.com/puttley/pxt-microbit-drone`
4. Select the extension to add the **Pitsco Drone** category to the toolbox.

## Minimal block sequence

1. Place `initialize drone link` in `on start`.
2. Use `drone is ready` before attempting to arm.
3. Use `arm drone` to open the bridge's 10-second authorization window.
4. Use `take off` during that window.
5. Use bounded movement blocks only after takeoff.
6. Use `land` to finish the flight.

The Python bridge must be running before a block that waits for a response is
executed.
