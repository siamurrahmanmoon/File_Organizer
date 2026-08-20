"""
core/profiles_manager.py - Preset Configuration Profiles Manager.
"""

from pathlib import Path
from typing import List, Optional
from config import OrganizerConfig, PRESETS_DIR


class ProfilesManager:
    """Manages saving, loading, exporting, and importing configuration presets."""

    def __init__(self, presets_dir: Path = PRESETS_DIR):
        self.presets_dir = presets_dir
        self.presets_dir.mkdir(parents=True, exist_ok=True)

    def list_presets(self) -> List[str]:
        """Returns list of preset profile names without .json extension."""
        presets = []
        try:
            for p in self.presets_dir.glob("*.json"):
                presets.append(p.stem)
        except Exception:
            pass
        return sorted(presets)

    def load_preset(self, name: str) -> Optional[OrganizerConfig]:
        """Loads an OrganizerConfig by preset name."""
        path = self.presets_dir / f"{name}.json"
        if not path.exists():
            return None
        try:
            return OrganizerConfig.load_profile(str(path))
        except Exception:
            return None

    def save_preset(self, name: str, config: OrganizerConfig) -> bool:
        """Saves an OrganizerConfig under the given preset name."""
        try:
            path = self.presets_dir / f"{name}.json"
            config.save_profile(str(path))
            return True
        except Exception:
            return False

    def delete_preset(self, name: str) -> bool:
        """Deletes a preset file."""
        try:
            path = self.presets_dir / f"{name}.json"
            if path.exists():
                path.unlink()
                return True
        except Exception:
            pass
        return False
