import tempfile
import wave

from datetime import datetime
from pathlib import Path
from typing import Callable, Iterator

import av

from transcriber.config import (
    TRANSCRIPTIONS_DIR,
    ensure_directories,
)

from transcriber.model import TranscriptionModel


CHUNK_DURATION_SECONDS = 300
SAMPLE_RATE = 16000


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

        return self.transcribe_with_progress(
            file_path=file_path,
        )

    def transcribe_with_progress(
        self,
        file_path: str,
        on_event: Callable[[dict], None] | None = None,
    ) -> Path:

        source = Path(file_path).expanduser().resolve()

        self._validate_source(source)

        ensure_directories()

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        output_path = TRANSCRIPTIONS_DIR / (
            f"{source.stem}_{timestamp}.txt"
        )

        duration = self._get_duration(source)

        total_chunks = max(
            1,
            int(
                (duration + CHUNK_DURATION_SECONDS - 1)
                // CHUNK_DURATION_SECONDS
            ),
        )

        self._emit(
            on_event,
            {
                "type": "transcription_started",
                "file": source.name,
                "duration": duration,
                "total_chunks": total_chunks,
            },
        )

        try:

            with output_path.open(
                "w",
                encoding="utf-8",
            ) as output:

                output.write(
                    f"Arquivo: {source.name}\n"
                )

                output.write(
                    f"Duração: {duration:.2f} segundos\n"
                )

                output.write(
                    "Idioma: pt\n\n"
                )

                for chunk_index, (
                    chunk_path,
                    offset,
                    chunk_duration,
                ) in enumerate(
                    self._extract_chunks(source),
                    start=1,
                ):

                    self._emit(
                        on_event,
                        {
                            "type": "segment_started",
                            "segment": chunk_index,
                            "total_segments": total_chunks,
                            "progress": (
                                (chunk_index - 1)
                                / total_chunks
                            ) * 100,
                        },
                    )

                    segments, _ = self.model.transcribe(
                        str(chunk_path),
                    )

                    chunk_text = []

                    for segment in segments:

                        start = offset + segment.start
                        end = offset + segment.end

                        text = segment.text.strip()

                        if not text:
                            continue

                        formatted_start = self._format_time(
                            start
                        )

                        formatted_end = self._format_time(
                            end
                        )

                        line = (
                            f"[{formatted_start} --> "
                            f"{formatted_end}] {text}"
                        )

                        output.write(line + "\n")

                        output.flush()

                        chunk_text.append(line)

                        self._emit(
                            on_event,
                            {
                                "type": "text_received",
                                "segment": chunk_index,
                                "text": line,
                            },
                        )

                    progress = (
                        chunk_index / total_chunks
                    ) * 100

                    self._emit(
                        on_event,
                        {
                            "type": "segment_completed",
                            "segment": chunk_index,
                            "total_segments": total_chunks,
                            "progress": round(progress, 2),
                            "text": "\n".join(chunk_text),
                        },
                    )

            self._emit(
                on_event,
                {
                    "type": "transcription_completed",
                    "file": str(output_path),
                    "progress": 100,
                },
            )

            return output_path

        except Exception as error:

            self._emit(
                on_event,
                {
                    "type": "transcription_error",
                    "message": str(error),
                },
            )

            raise

    @staticmethod
    def _validate_source(source: Path) -> None:

        if not source.exists():

            raise FileNotFoundError(
                f"Arquivo não encontrado: {source}"
            )

        if not source.is_file():

            raise ValueError(
                "O caminho informado não é um arquivo."
            )

    @staticmethod
    def _get_duration(source: Path) -> float:

        with av.open(str(source)) as container:

            if not container.streams.audio:

                raise ValueError(
                    "O arquivo não possui uma faixa de áudio."
                )

            stream = container.streams.audio[0]

            if stream.duration is not None:

                return float(
                    stream.duration * stream.time_base
                )

            if container.duration is not None:

                return float(
                    container.duration / av.time_base
                )

            raise ValueError(
                "Não foi possível identificar a duração do áudio."
            )

    @staticmethod
    def _extract_chunks(
        source: Path,
    ) -> Iterator[tuple[Path, float, float]]:

        chunk_samples = (
            CHUNK_DURATION_SECONDS * SAMPLE_RATE
        )

        bytes_per_sample = 2

        chunk_bytes = chunk_samples * bytes_per_sample

        buffer = bytearray()

        offset = 0.0

        with tempfile.TemporaryDirectory() as temp_dir:

            temp_path = Path(temp_dir)

            with av.open(str(source)) as container:

                audio_stream = container.streams.audio[0]

                resampler = av.AudioResampler(
                    format="s16",
                    layout="mono",
                    rate=SAMPLE_RATE,
                )

                def write_chunk(
                    pcm_data: bytes,
                    chunk_number: int,
                    chunk_offset: float,
                ) -> Path:

                    chunk_path = (
                        temp_path / f"chunk_{chunk_number}.wav"
                    )

                    with wave.open(
                        str(chunk_path),
                        "wb",
                    ) as audio_file:

                        audio_file.setnchannels(1)
                        audio_file.setsampwidth(2)
                        audio_file.setframerate(SAMPLE_RATE)

                        audio_file.writeframes(pcm_data)

                    return chunk_path

                chunk_number = 0

                for frame in container.decode(audio_stream):

                    resampled_frames = resampler.resample(
                        frame
                    )

                    for resampled_frame in resampled_frames:

                        buffer.extend(
                            resampled_frame.to_ndarray().tobytes()
                        )

                    while len(buffer) >= chunk_bytes:

                        chunk_number += 1

                        pcm_data = bytes(
                            buffer[:chunk_bytes]
                        )

                        chunk_path = write_chunk(
                            pcm_data,
                            chunk_number,
                            offset,
                        )

                        yield (
                            chunk_path,
                            offset,
                            CHUNK_DURATION_SECONDS,
                        )

                        del buffer[:chunk_bytes]

                        offset += CHUNK_DURATION_SECONDS

                # Descarrega os últimos frames do resampler.
                for frame in resampler.resample(None):

                    buffer.extend(
                        frame.to_ndarray().tobytes()
                    )

                # Processa o último segmento, mesmo que menor.
                if buffer:

                    chunk_number += 1

                    remaining_duration = (
                        len(buffer)
                        / bytes_per_sample
                        / SAMPLE_RATE
                    )

                    chunk_path = write_chunk(
                        bytes(buffer),
                        chunk_number,
                        offset,
                    )

                    yield (
                        chunk_path,
                        offset,
                        remaining_duration,
                    )

    @staticmethod
    def _emit(
        callback: Callable[[dict], None] | None,
        event: dict,
    ) -> None:

        if callback is not None:
            callback(event)

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