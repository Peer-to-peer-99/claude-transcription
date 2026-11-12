from datetime import datetime
from pathlib import Path

from transcriber.config import (
    TRANSCRIPTIONS_DIR,
    ensure_directories,
)

from transcriber.model import TranscriptionModel


class TranscriptionService:

    def __init__(
        self,
        model_size: str = "small",
    ) -> None:

        self.model = TranscriptionModel(
            model_size=model_size,
        )

    def transcribe(
        self,
        file_path: str,
    ) -> Path:

        source = Path(file_path).expanduser().resolve()

        if not source.exists():
            raise FileNotFoundError(
                f"Arquivo não encontrado: {source}"
            )

        if not source.is_file():
            raise ValueError(
                "O caminho informado não é um arquivo."
            )

        ensure_directories()

        segments, info = self.model.transcribe(
            str(source),
        )

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        output_path = TRANSCRIPTIONS_DIR / (
            f"{source.stem}_{timestamp}.txt"
        )

        with output_path.open(
            "w",
            encoding="utf-8",
        ) as file:

            file.write(
                f"Arquivo: {source.name}\n"
            )

            file.write(
                f"Idioma: {info.language}\n"
            )

            file.write(
                f"Duração: {info.duration:.2f} segundos\n\n"
            )

            for segment in segments:

                start = self._format_time(
                    segment.start
                )

                end = self._format_time(
                    segment.end
                )

                text = segment.text.strip()

                file.write(
                    f"[{start} --> {end}] {text}\n"
                )

        return output_path

    @staticmethod
    def _format_time(seconds: float) -> str:

        milliseconds = int(seconds * 1000)

        hours = milliseconds // 3_600_000

        minutes = (
            milliseconds % 3_600_000
        ) // 60_000

        seconds = (
            milliseconds % 60_000
        ) // 1000

        milliseconds %= 1000

        return (
            f"{hours:02}:"
            f"{minutes:02}:"
            f"{seconds:02},"
            f"{milliseconds:03}"
        )