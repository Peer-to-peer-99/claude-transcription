from faster_whisper import WhisperModel

from transcriber.config import (
    DEFAULT_COMPUTE_TYPE,
    DEFAULT_DEVICE,
    WHISPER_CACHE_DIR,
    ensure_directories,
)


class TranscriptionModel:

    def __init__(
        self,
        model_size: str = "small",
        device: str = DEFAULT_DEVICE,
        compute_type: str = DEFAULT_COMPUTE_TYPE,
    ) -> None:

        ensure_directories()

        self.model_size = model_size

        self.model = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type,
            download_root=str(WHISPER_CACHE_DIR),
        )

    def transcribe(self, file_path: str):

        return self.model.transcribe(
            file_path,
            beam_size=5,
            vad_filter=True,
            condition_on_previous_text=False,
            language="pt",
        )