"""
utils/venv_utils.py - Enforces execution inside the project's virtual environment (venv).
"""

import sys
import os
import subprocess
from pathlib import Path


def ensure_venv():
    """
    Checks if the script is running inside the project's virtual environment (venv).
    If executed outside venv, automatically re-launches itself using venv/Scripts/python.exe.
    """
    # Prevent infinite relaunch loops
    if os.environ.get("_ORGANIZER_VENV_ACTIVE") == "1":
        return

    base_dir = Path(__file__).resolve().parent.parent
    venv_dir = base_dir / "venv"

    if sys.platform == "win32":
        venv_python = venv_dir / "Scripts" / "python.exe"
    else:
        venv_python = venv_dir / "bin" / "python"

    if venv_python.exists():
        try:
            current_python = Path(sys.executable).resolve()
            target_python = venv_python.resolve()

            if current_python != target_python:
                # Re-launch with venv python
                env = os.environ.copy()
                env["_ORGANIZER_VENV_ACTIVE"] = "1"
                cmd = [str(target_python)] + sys.argv
                result = subprocess.run(cmd, env=env)
                sys.exit(result.returncode)
        except Exception as e:
            # If re-launch check fails, continue with current python
            pass
