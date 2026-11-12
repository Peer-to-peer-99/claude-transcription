from faster_whisper import WhisperModel

from transcriber.config import (
    DEFAULT_COMPUTE_TYPE,
    DEFAULT_DEVICE,
)


class TranscriptionModel:

    def __init__(
        self,
        model_size: str = "small",
        device: str = DEFAULT_DEVICE,
        compute_type: str = DEFAULT_COMPUTE_TYPE,
    ) -> None:

        self.model_size = model_size

        self.model = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type,
        )

    def transcribe(self, file_path: str):

        return self.model.transcribe(
            file_path,
            beam_size=5,
            vad_filter=True,
            condition_on_previous_text=False,
            language="pt",
        )