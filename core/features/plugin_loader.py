"""
Plugin System — auto-discovers and loads Python plugins from the plugins/ directory.
Plugins are simple .py files with a `register(bot, session)` function.
"""

import importlib
import inspect
import os
import sys
import traceback
from pathlib import Path

from ..config import PLUGINS_ENABLED, PLUGIN_DIR
from .. import db


class PluginLoader:
    """Scans plugins/ folder, loads & tracks enabled plugins."""

    def __init__(self, on_log=None):
        self._log = on_log or (lambda *a: None)
        self._loaded = {}  # {name: module}

    def discover(self) -> list[dict]:
        """Return metadata about all available plugins."""
        plugins = []
        if not PLUGINS_ENABLED:
            return plugins
        PLUGIN_DIR.mkdir(parents=True, exist_ok=True)

        # Create __init__.py if missing
        init_file = PLUGIN_DIR / "__init__.py"
        if not init_file.exists():
            init_file.write_text("")

        for f in sorted(PLUGIN_DIR.glob("*.py")):
            if f.name == "__init__.py":
                continue
            plugins.append({
                "name": f.stem,
                "path": str(f),
                "enabled": True,
                "version": "1.0",
            })
        return plugins

    def load_all(self, session_ref):
        """Load all plugin modules and call their register() function."""
        if not PLUGINS_ENABLED:
            return
        sys.path.insert(0, str(PLUGIN_DIR.parent))
        for f in sorted(PLUGIN_DIR.glob("*.py")):
            if f.name == "__init__.py":
                continue
            try:
                mod_name = f"plugins.{f.stem}"
                if mod_name in sys.modules:
                    mod = importlib.reload(sys.modules[mod_name])
                else:
                    mod = importlib.import_module(mod_name)

                if hasattr(mod, "register"):
                    mod.register(session_ref)
                    self._loaded[f.stem] = mod
                    db.register_plugin(f.stem)
                    self._log("plugin", f"🔌 Loaded plugin: {f.stem}")
                else:
                    self._log("plugin", f"⚠️ Plugin {f.stem} has no register() function")
            except Exception as e:
                self._log("plugin", f"❌ Plugin {f.stem} error: {e}")

    def get_help_text(self) -> str:
        """Collect help text from loaded plugins that have a help_text attribute."""
        lines = []
        for name, mod in self._loaded.items():
            text = getattr(mod, "help_text", None)
            if text:
                lines.append(text)
        return "\n".join(lines)

    def get_commands(self) -> list[tuple[str, str]]:
        """Return [(command, description)] from plugins."""
        cmds = []
        for name, mod in self._loaded.items():
            fn = getattr(mod, "commands", None)
            if fn and callable(fn):
                cmds.extend(fn())
        return cmds
