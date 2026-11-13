import argparse
import json
import sys

from transcriber.service import TranscriptionService


def handle_event(event: dict, json_events: bool = False) -> None:
    if json_events:
        print(
            json.dumps(event, ensure_ascii=False),
            flush=True,
        )
        return

    event_type = event["type"]

    if event_type == "transcription_started":
        print("\nIniciando transcrição...")
        print(f"Arquivo: {event['file']}")
        print(f"Segmentos previstos: {event['total_chunks']}\n")

    elif event_type == "segment_started":
        print(
            f"\nProcessando segmento "
            f"{event['segment']}/{event['total_segments']}..."
        )

    elif event_type == "text_received":
        print(event["text"], flush=True)

    elif event_type == "segment_completed":
        print(
            f"\nProgresso: {event['progress']}%",
            flush=True,
        )

    elif event_type == "transcription_completed":
        print("\nTranscrição concluída.")

    elif event_type == "transcription_error":
        print(
            f"\nErro: {event['message']}",
            file=sys.stderr,
            flush=True,
        )


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
        choices=["tiny", "base", "small", "medium", "large-v3"],
        help="Modelo Whisper utilizado.",
    )

    parser.add_argument(
        "--json-events",
        action="store_true",
        help="Emite eventos JSON para integração com o desktop.",
    )

    args = parser.parse_args()

    try:
        service = TranscriptionService(
            model_size=args.model,
        )

        output = service.transcribe_with_progress(
            file_path=args.file,
            on_event=lambda event: handle_event(
                event,
                json_events=args.json_events,
            ),
        )

        if not args.json_events:
            print(f"\nResultado: {output}")

    except Exception as error:
        if args.json_events:
            print(
                json.dumps(
                    {
                        "type": "transcription_error",
                        "message": str(error),
                    },
                    ensure_ascii=False,
                ),
                flush=True,
            )
        else:
            print(f"\nErro: {error}", file=sys.stderr)

        sys.exit(1)


if __name__ == "__main__":
    main()