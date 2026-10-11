"""Build the SwitchBot Meter pocket into ./output/.

uv run python -m hooks.switchbot_meter.build
"""

from . import pocket

if __name__ == "__main__":
    pocket.main()
