# microbit-drone

Experimental Microsoft MakeCode blocks for guarded control of a Crazyflie 2.1
through a USB-connected micro:bit and a Python PC bridge.

## Current blocks

- `initialize drone link`
- `drone is ready`
- `arm one test flight`
- `disarm drone`
- `run armed test flight`
- `last drone response` (advanced)

## Safety model

The initial flight command is deliberately constrained. The Python bridge only
accepts `TEST_FLIGHT` during a 10-second authorization window opened by `ARM`.
Authorization is consumed before takeoff. The aircraft takes off to 0.4 m,
hovers for five seconds, and lands automatically.

## Architecture

`MakeCode blocks -> micro:bit USB serial -> Python bridge -> Crazyradio -> Crazyflie`

This version is PC-tethered and does not communicate directly from the
micro:bit to the Crazyflie radio.

## Add to MakeCode

1. Open the micro:bit MakeCode editor.
2. Select **Extensions**.
3. Paste this repository URL into the search box:
   `https://github.com/puttley/pxt-microbit-drone`
4. Select the extension to add the **Drone** category to the toolbox.

## Minimal block sequence

1. Place `initialize drone link` in `on start`.
2. Use `drone is ready` before attempting to arm.
3. Use `arm one test flight` to open the bridge's 10-second authorization
   window.
4. Use `run armed test flight` during that window.

The Python bridge must be running before a block that waits for a response is
executed.
