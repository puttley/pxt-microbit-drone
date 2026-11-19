# Pitsco Drone serial protocol v1

Protocol v1 is the validated command contract between the MakeCode extension
and the Python development bridge. It is frozen by extension release `v0.5.0`
and is the starting contract for the future nRF52 radio coprocessor.

## Transport and framing

- USB CDC serial at 115200 baud, 8 data bits, no parity, and 1 stop bit.
- Commands and responses are UTF-8/ASCII text records terminated by LF.
- The bridge treats command text as case-insensitive.
- Only one request that expects a response may be outstanding at a time.
- Every request receives exactly one response except `HEARTBEAT`, which has no
  response.

## State model

The bridge exposes these flight states:

- `GROUND`
- `ARMED`
- `TAKING_OFF`
- `AIRBORNE`
- `LANDING`
- `FAULT`

Arming is valid for 10 seconds and is consumed by `TAKEOFF`. Takeoff targets
0.40 m. While airborne, the controller sends `HEARTBEAT` every 500 ms. Missing
heartbeats for 2 seconds initiates a controlled landing.

## Commands

| Command | Successful response | Notes |
| --- | --- | --- |
| `STATUS` | `READY` | Requires the Flow Deck and no bridge fault. |
| `FLIGHT_STATUS` | Current state | Returns one of the states listed above. |
| `ARM` | `ARMED` | Accepted only from `GROUND`. |
| `DISARM` | `DISARMED` | Accepted from `GROUND` or `ARMED`. |
| `TAKEOFF` | `AIRBORNE` | Requires an unexpired arm authorization. |
| `LAND` | `LANDED` | A ground-state landing is idempotent. |
| `MOVE:<direction>:<cm>` | `MOVED` | Direction is `FORWARD`, `BACKWARD`, `LEFT`, or `RIGHT`; distance is 5-50 cm. |
| `TURN:<direction>:<degrees>` | `TURNED` | Direction is `LEFT` or `RIGHT`; angle is 15-180 degrees. |
| `ALTITUDE:<direction>:<cm>` | `ALTITUDE_CHANGED` | Direction is `UP` or `DOWN`; step is 5-30 cm. |
| `HEARTBEAT` | None | Refreshes liveness only while `AIRBORNE`. |
| `TEST_FLIGHT` | `LANDED` | Legacy guarded takeoff, five-second hover, and landing. |

Horizontal speed is fixed at 0.2 m/s. Turn rate is fixed at 72 degrees/s.
Vertical speed is fixed at 0.2 m/s. The bridge tracks commanded altitude and
rejects any altitude step that would put the target below 0.25 m or above
1.00 m.

## Error responses

The bridge may return:

- `NOT_READY:NO_FLOW2`
- `NOT_READY:FAULT`
- `NOT_ARMED`
- `ERROR:STATE:<state>`
- `ERROR:DIRECTION`
- `ERROR:DISTANCE`
- `ERROR:ANGLE`
- `ERROR:ALTITUDE_LIMIT`
- `ERROR:FORMAT`
- `UNKNOWN:<command>`
- `FLIGHT_ERROR`

The MakeCode extension stores the last received response for diagnostics.

## Safety boundary

The heartbeat and cleanup landings are development safety layers. They depend
on the bridge, radio link, Crazyflie firmware, estimator, motors, and available
power remaining functional. They do not replace an independent hardware stop
path or the Crazyflie firmware supervisor.
