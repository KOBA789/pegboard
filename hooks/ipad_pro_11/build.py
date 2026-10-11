"""Build the iPad Pro 11 holder into ./output/.

uv run python -m hooks.ipad_pro_11.build
"""

from . import holder

if __name__ == "__main__":
    holder.main()
