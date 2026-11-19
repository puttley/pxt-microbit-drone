# Pitsco handheld controller Rev A

Rev A is a micro:bit-based handheld controller intended to prove direct radio
control of a stock Crazyflie without a PC or Crazyradio. It is also the input
and radio platform for the future dual-purpose DRONE/ROVER vehicle.

## Locked requirements

- Plug-in micro:bit V2 using a full edge connector
- Two dual-axis 10 kOhm joysticks
- Four external face buttons
- One dedicated radio safety button
- Two replaceable AA cells
- Four-channel joystick ADC accessible to MakeCode
- nRF52840 radio coprocessor with SWD programming
- Bidirectional UART between micro:bit and nRF52840
- JLCPCB assembly and LCSC parts where practical
- Hand-installed mechanical controls and connectors are acceptable
- Schematic and PCB entry in EasyEDA Desktop Standard, not EasyEDA Pro

## Architecture

```text
2xAA -> protection -> 3.3 V buck-boost
                         |-- nRF52840 radio module
                         |-- ADS1015 joystick ADC
                         `-- isolated feed to micro:bit VDD

Joysticks -> ADS1015 -> I2C -> micro:bit
Buttons --------------------> micro:bit GPIO
micro:bit <------ UART -----> nRF52840 -> ESB/CRTP -> Crazyflie
Safety button --------------> nRF52840
```

## Rev-A core parts

| Function | Part | LCSC |
| --- | --- | --- |
| Radio | Ebyte E73-2G4M08S1C | C356849 |
| Joystick ADC | TI ADS1015IDGSR | C193969 |
| 3.3 V buck-boost | TI TPS63031DSKR | C15516 |

The E73 is a prototype choice. Re-evaluate its Nordic silicon revision,
certification, sourcing, and antenna performance before production.

## MakeCode-facing pin allocation

| micro:bit edge pin | Rev-A function |
| --- | --- |
| P8 | UART TX to nRF RX |
| P12 | UART RX from nRF TX |
| P13 | Left face button 1 |
| P14 | Left face button 2 |
| P15 | Right face button 1 |
| P16 | Right face button 2 |
| P19 | External I2C SCL |
| P20 | External I2C SDA |

## Schematic sheets

1. `POWER` - battery input, protection, switching regulator, rail isolation
2. `MICROBIT` - edge connector, UART, I2C, buttons, test points
3. `CONTROLS` - joysticks, filters, ADS1015, optional routing
4. `RADIO` - E73 module, SWD, reset, safety input, status LED

In EasyEDA Standard these may be implemented as separate schematic sheets if
that fits the local workflow, or as clearly labeled functional frames on one
sheet. Do not rely on Pro-only managed libraries or hierarchical-block
features. Search the Standard/LCSC library by the exact `C` part numbers, then
verify every symbol-to-footprint mapping against the manufacturer datasheet.

## Assembly plan

JLCPCB should assemble the regulator, ADC, radio module, passives, and small
SMD protection parts. The micro:bit socket, joysticks, AA holder/connector,
face buttons, power switch, and safety button may be hand-installed.

## Open mechanical selections

- Exact joystick manufacturer and footprint
- Exact micro:bit edge socket
- Face and safety button cap/footprint
- AA holder mounting and lead/connector style
- Enclosure outline, mounting holes, and joystick center spacing

Do not begin final PCB placement until the joystick and edge-socket footprints
have been verified against physical samples.
