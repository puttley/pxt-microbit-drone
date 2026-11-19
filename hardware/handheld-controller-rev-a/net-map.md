# Rev-A schematic net map

This is the source-of-truth connection plan for EasyEDA entry. Pin numbers and
footprints must still be checked against current manufacturer drawings.

## Named power nets

- `VBAT_RAW` - two-AA holder output
- `VBAT_PROTECTED` - after reverse-polarity protection
- `+3V3_CTRL` - regulated controller rail
- `MB_VDD` - isolated micro:bit supply rail
- `GND` - common ground

## Power section

### Battery and protection

- Two-AA holder positive -> `VBAT_RAW`
- Two-AA holder negative -> `GND`
- `VBAT_RAW` -> Q1 reverse-polarity stage -> `VBAT_PROTECTED`
- Add battery input test point and optional bulk capacitor footprint

### TPS63031

- `VBAT_PROTECTED` -> VIN/VINA and input bypass network
- 1.5 uH L1 between the regulator switching pins per TI reference design
- VOUT -> `+3V3_CTRL`
- Place input ceramic capacitance adjacent to VIN/PGND
- Place two output ceramic capacitors adjacent to VOUT/PGND
- Tie PS/SYNC for power-save operation unless testing proves otherwise
- Main switch drives EN; include a defined EN pull-down
- Follow the TI datasheet layout rather than autorouter placement

### micro:bit rail isolation

- `+3V3_CTRL` -> D1 low-drop Schottky -> `MB_VDD`
- `MB_VDD` -> micro:bit 3V edge pins
- The diode prevents micro:bit USB power from driving the controller rail
- Add `MB_VDD` and `+3V3_CTRL` test points
- Check the selected diode drop with the maximum micro:bit load before release

## micro:bit edge connections

- All micro:bit GND contacts -> `GND`
- All micro:bit 3V contacts -> `MB_VDD`
- P8 -> R series -> `MB_UART_TX`
- P12 <- R series <- `MB_UART_RX`
- P13 -> `BTN_L1_N`
- P14 -> `BTN_L2_N`
- P15 -> `BTN_R1_N`
- P16 -> `BTN_R2_N`
- P19 -> `I2C_SCL`
- P20 -> `I2C_SDA`
- Add labeled test pads for UART and I2C

Use approximately 1 kOhm series footprints on both UART signals for Rev A.

## Four face buttons

For each button input:

- 10 kOhm pull-up from the button net to `MB_VDD`
- Normally-open button from the button net to `GND`
- Optional 10-100 nF capacitor from the button net to `GND`
- Software performs final debounce and event generation

## I2C and ADS1015

- ADS1015 VDD -> `+3V3_CTRL`
- ADS1015 GND -> `GND`
- ADS1015 SDA -> `I2C_SDA`
- ADS1015 SCL -> `I2C_SCL`
- 4.7 kOhm pull-ups from SDA and SCL to `MB_VDD`
- ADS1015 ADDR -> `GND` for address `0x48`
- ADS1015 ALERT/RDY -> labeled test point; otherwise unused
- 100 nF local bypass at ADS1015 VDD

## Joysticks

For each 10 kOhm potentiometer axis:

- High terminal -> `+3V3_CTRL`
- Low terminal -> `GND`
- Wiper -> 1 kOhm series resistor -> filtered axis net
- 100 nF optional capacitor from filtered axis net to `GND`

Default axis routing:

| Axis | ADS1015 input | Optional nRF input |
| --- | --- | --- |
| `JOY_LX` | AIN0 | E73 pin 4 / P0.28 AIN4 |
| `JOY_LY` | AIN1 | E73 pin 8 / P0.29 AIN5 |
| `JOY_RX` | AIN2 | E73 pin 10 / P0.30 AIN6 |
| `JOY_RY` | AIN3 | E73 pin 9 / P0.31 AIN7 |

Provide two mutually exclusive 0 Ohm options per axis: ADS1015 populated by
default, nRF route DNP. Do not populate both routes during initial testing.

## E73 nRF52840 module

Prototype pin allocation:

| E73 module pad | nRF signal | Rev-A function |
| --- | --- | --- |
| 5, 21, 24 | GND | `GND` |
| 19 | VDD | `+3V3_CTRL` |
| 14 | P0.06 | UART RX from `MB_UART_TX` |
| 16 | P0.08 | UART TX to `MB_UART_RX` |
| 1 | P1.11 | `SAFETY_BTN_N` |
| 2 | P1.10 | `RADIO_STATUS_LED` |
| 7 | P0.02/AIN0 | divided battery measurement |
| 26 | P0.18/RESET | reset/test/programming |
| 37 | SWDIO | programming connector |
| 39 | SWDCLK | programming connector |

- Safety input: 10 kOhm pull-up to `+3V3_CTRL`, normally-open switch to GND
- Add optional RC debounce to the safety input
- Status LED uses a current-limiting resistor
- Add 100 nF plus local bulk decoupling adjacent to module supply pads
- Leave VDDH, VBUS, USB, NFC, and DC/DC-specific pins unconnected unless the
  final module reference circuit explicitly requires otherwise
- Initial firmware may use the internal LFRC; reserve optional 32.768 kHz
  crystal footprints only if layout space permits

## Battery measurement

- `VBAT_PROTECTED` -> high-value divider -> E73 P0.02/AIN0
- Add a capacitor at the ADC node for sampling stability
- Ensure the divider cannot back-power an unpowered nRF
- Final divider values will be selected during power-sheet completion

## RF layout rules

- Place the E73 antenna end at or beyond a PCB edge
- No copper, traces, planes, components, battery metal, or mounting hardware in
  the antenna keepout on any layer
- Keep regulator switching nodes and joystick traces away from the antenna
- Do not place the AA cells immediately behind the antenna
- Verify the EasyEDA footprint against the Ebyte mechanical drawing
