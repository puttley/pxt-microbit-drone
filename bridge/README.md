# Python development bridge

This bridge connects the micro:bit USB serial port to a Crazyflie through a
Crazyradio. It is the validated development transport for the MakeCode
extension; the production radio coprocessor will implement the same logical
commands without requiring a PC.

From the repository root on Windows, run:

```powershell
uv run --python 3.12 --with cflib --with pyserial python .\bridge\microbit_crazyflie_bridge.py --port COM16
```

Change `COM16` if Windows assigns the micro:bit a different port. The default
Crazyflie URI is `radio://0/80/2M`; override it with `--uri` when needed.

Run the hardware-independent state-machine tests with:

```powershell
uv run --python 3.12 --with cflib --with pyserial python -m unittest discover -s .\bridge -p "test_*.py" -v
```

See [protocol-v1.md](../docs/protocol-v1.md) for the serial command contract.
