from pathlib import Path
from types import SimpleNamespace

from transcriber.service import TranscriptionService


class FakeModel:

    def transcribe(self, file_path):

        segments = [
            SimpleNamespace(
                start=0.0,
                end=2.5,
                text=" Primeiro depoimento.",
            ),
            SimpleNamespace(
                start=2.5,
                end=5.0,
                text=" Segundo depoimento.",
            ),
        ]

        info = SimpleNamespace(
            language="pt",
            duration=5.0,
        )

        return segments, info


def test_transcription_creates_file(tmp_path, monkeypatch):

    import transcriber.service as service_module

    monkeypatch.setattr(
        service_module,
        "TRANSCRIPTIONS_DIR",
        tmp_path,
    )

    monkeypatch.setattr(
        service_module,
        "ensure_directories",
        lambda: None,
    )

    service = TranscriptionService.__new__(
        TranscriptionService
    )

    service.model = FakeModel()

    source = tmp_path / "audiencia.mp3"

    source.write_bytes(b"fake audio")

    output = service.transcribe(
        str(source)
    )

    assert output.exists()

    content = output.read_text(
        encoding="utf-8"
    )

    assert "Primeiro depoimento." in content

    assert "Segundo depoimento." in content

    assert "Idioma: pt" in content


def test_transcription_rejects_missing_file():

    service = TranscriptionService.__new__(
        TranscriptionService
    )

    service.model = FakeModel()

    try:

        service.transcribe(
            "arquivo-inexistente.mp3"
        )

        assert False, "Era esperado FileNotFoundError."

    except FileNotFoundError:

        assert True