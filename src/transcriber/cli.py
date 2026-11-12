import argparse
import sys

from transcriber.service import TranscriptionService


def main() -> None:

    parser = argparse.ArgumentParser(
        description="Transcrição local de áudio e vídeo."
    )

    parser.add_argument(
        "file",
        help="Caminho do arquivo de áudio ou vídeo.",
    )

    parser.add_argument(
        "--model",
        default="small",
        choices=[
            "tiny",
            "base",
            "small",
            "medium",
            "large-v3",
        ],
        help="Modelo Whisper utilizado.",
    )

    args = parser.parse_args()

    try:

        print("Iniciando transcrição...")

        service = TranscriptionService(
            model_size=args.model,
        )

        output = service.transcribe(
            args.file,
        )

        print("\nTranscrição concluída.")

        print(f"Resultado: {output}")

    except Exception as error:

        print(
            f"\nErro: {error}",
            file=sys.stderr,
        )

        sys.exit(1)


if __name__ == "__main__":
    main()