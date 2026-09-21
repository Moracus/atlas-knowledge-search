import os
from pathlib import Path

CONFIG_DIR = Path(os.environ.get("ATLAS_HOME", Path.home() / ".atlas")).expanduser()
CONFIG_FILE = CONFIG_DIR / "config.env"