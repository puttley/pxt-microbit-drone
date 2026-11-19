# Rev-A schematic and layout review checklist

## Before schematic release

- [ ] Verify every E73 pad number against the E73-2G4M08S1C manual
- [ ] Verify ADS1015 pinout and address strap
- [ ] Verify TPS63031 exposed pad, inductor, capacitors, and PS/SYNC state
- [ ] Select a reverse-polarity device that works at two-cell end voltage
- [ ] Select and calculate the micro:bit isolation diode drop
- [ ] Confirm micro:bit V2 supply voltage under worst-case controller load
- [ ] Confirm UART logic levels when USB and batteries are both present
- [ ] Verify all edge-connector power and ground contacts
- [ ] Confirm P13-P16 do not conflict with required MakeCode peripherals
- [ ] Select battery-divider values and calculate off-state leakage
- [ ] Add accessible UART, I2C, rail, reset, and SWD test points
- [ ] Add mounting holes and enclosure ground/clearance notes

## Before PCB release

- [ ] Measure physical joystick samples and verify the footprint
- [ ] Test-fit the physical micro:bit socket and board thickness
- [ ] Orient the micro:bit so USB and buttons remain accessible
- [ ] Place joysticks symmetrically for the intended enclosure
- [ ] Put the E73 antenna at the board edge with an all-layer keepout
- [ ] Keep the TPS63031 hot loop compact and away from RF/analog circuits
- [ ] Keep joystick filtered nets short and away from switching nodes
- [ ] Use a solid ground plane except in the antenna keepout
- [ ] Place decoupling before routing signals
- [ ] Confirm battery holder metal does not overlap the RF keepout
- [ ] Confirm silkscreen identifies all controls and polarity
- [ ] Add revision, date, programming orientation, and test-point labels

## Before ordering from JLCPCB

- [ ] Recheck current JLC assembly inventory for every LCSC number
- [ ] Confirm Basic/Extended classifications and associated setup fees
- [ ] Validate BOM and CPL rotations in JLC's 3D/assembly preview
- [ ] Confirm the E73 module is accepted for assembly on the selected side
- [ ] Verify exposed-pad paste apertures for TPS63031
- [ ] Exclude hand-installed parts from the assembly BOM/CPL
- [ ] Order at least one extra bare PCB for probing and rework
