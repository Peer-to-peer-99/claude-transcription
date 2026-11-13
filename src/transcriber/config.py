import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

TRANSCRIPTIONS_DIR = Path(
    os.environ.get(
        "CLAUDE_AUDIENCIA_TRANSCRIPTIONS_DIR",
        PROJECT_ROOT / "transcriptions",
    )
).expanduser()

WHISPER_CACHE_DIR = Path(
    os.environ.get(
        "CLAUDE_AUDIENCIA_MODEL_DIR",
        Path.home() / ".cache" / "claude-audiencia" / "models",
    )
).expanduser()

DEFAULT_MODEL = "small"
DEFAULT_DEVICE = "cpu"
DEFAULT_COMPUTE_TYPE = "int8"


def ensure_directories() -> None:
    TRANSCRIPTIONS_DIR.mkdir(parents=True, exist_ok=True)
    WHISPER_CACHE_DIR.mkdir(parents=True, exist_ok=True)