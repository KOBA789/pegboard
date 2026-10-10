import importlib.util
from pathlib import Path

ROOT = Path(__file__).parent.parent


def load_hook(name: str):
    """Import hooks/<name>/build.py as a module."""
    path = ROOT / "hooks" / name / "build.py"
    spec = importlib.util.spec_from_file_location(f"hooks.{name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
