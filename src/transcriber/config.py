from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

TRANSCRIPTIONS_DIR = PROJECT_ROOT / "transcriptions"

DEFAULT_MODEL = "small"

DEFAULT_DEVICE = "cpu"

DEFAULT_COMPUTE_TYPE = "int8"


def ensure_directories() -> None:
    TRANSCRIPTIONS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )