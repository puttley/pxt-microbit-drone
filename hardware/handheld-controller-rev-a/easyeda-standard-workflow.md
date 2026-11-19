# EasyEDA Desktop Standard workflow

This project targets EasyEDA Desktop Standard.

1. Create a local Standard project named `Pitsco-Handheld-Controller-Rev-A`.
2. Create functional schematic sheets or labeled sections for `POWER`,
   `MICROBIT`, `CONTROLS`, and `RADIO`.
3. Search the integrated library using exact LCSC numbers:
   - `C356849` - E73-2G4M08S1C
   - `C193969` - ADS1015IDGSR
   - `C15516` - TPS63031DSKR
4. Copy any accepted library item into a project/personal library before
   making corrections. Do not modify a public/community item in place.
5. Compare symbol pins and footprint pad numbers to the manufacturer drawing.
6. Use the net names in `net-map.md` exactly; avoid unnamed long wires between
   functional sections.
7. Run the Standard ERC and resolve or explicitly mark every warning.
8. Convert the checked schematic to PCB only after the joystick and micro:bit
   socket footprints have been verified using physical samples.
9. Add the E73 antenna keepout manually on all copper layers and document it on
   the mechanical/silkscreen layer.
10. Export the Standard BOM and pick-and-place files, then compare them with
    `bom-draft.csv` before uploading to JLCPCB.

The Markdown and CSV files are the design source of truth until a reviewed
EasyEDA Standard project is committed alongside them.
