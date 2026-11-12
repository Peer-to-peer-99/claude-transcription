import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

VENV_DIR = ROOT / ".venv"


def run(command: list[str]) -> None:

    print(f"\nExecutando: {' '.join(command)}")

    subprocess.run(
        command,
        cwd=ROOT,
        check=True,
    )


def get_venv_python() -> Path:

    if os.name == "nt":

        return (
            VENV_DIR
            / "Scripts"
            / "python.exe"
        )

    return (
        VENV_DIR
        / "bin"
        / "python"
    )


def create_environment() -> None:

    print("\n[1/4] Criando ambiente virtual...")

    if not VENV_DIR.exists():

        run([
            sys.executable,
            "-m",
            "venv",
            str(VENV_DIR),
        ])


def install_dependencies() -> None:

    python = get_venv_python()

    print("\n[2/4] Atualizando pip...")

    run([
        str(python),
        "-m",
        "pip",
        "install",
        "--upgrade",
        "pip",
    ])

    print("\n[3/4] Instalando projeto e dependências...")

    run([
        str(python),
        "-m",
        "pip",
        "install",
        "-e",
        ".",
    ])


def validate_installation() -> None:

    python = get_venv_python()

    print("\n[4/4] Validando instalação...")

    run([
        str(python),
        "-c",
        (
            "from faster_whisper import WhisperModel; "
            "from transcriber.service import TranscriptionService; "
            "print('Dependências verificadas com sucesso.')"
        ),
    ])

def download_default_model() -> None:

    print("\nBaixando modelo Whisper...")

    python = get_venv_python()

    run([
        str(python),
        "-c",
        (
            "from transcriber.model import TranscriptionModel; "
            "TranscriptionModel(model_size='small'); "
            "print('Modelo baixado com sucesso.')"
        ),
    ])

def main() -> None:

    try:

        print("=" * 50)
        print(" CLAUDE AUDIÊNCIA - INSTALADOR")
        print("=" * 50)

        create_environment()

        install_dependencies()

        validate_installation()
        
        download_default_model()

        print("\nInstalação concluída!")

        print(
            "O ambiente está preparado para uso."
        )

    except subprocess.CalledProcessError as error:

        print(
            f"\nFalha durante a instalação: {error}"
        )

        sys.exit(1)


if __name__ == "__main__":
    main()