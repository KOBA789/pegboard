"""Build both keyboard holders into ./output/.

uv run python -m hooks.trackpoint_keyboard.build
"""

from . import cradle, shelf

if __name__ == "__main__":
    cradle.main()
    shelf.main()
