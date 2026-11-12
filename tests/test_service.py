from pathlib import Path

from transcriber.service import TranscriptionService


class FakeSegment:

    def __init__(
        self,
        start: float,
        end: float,
        text: str,
    ):
        self.start = start
        self.end = end
        self.text = text


class FakeModel:

    def transcribe(self, file_path: str):

        segments = [
            FakeSegment(
                start=0,
                end=5,
                text=" Transcrição de teste.",
            )
        ]

        return iter(segments), None


def test_transcription_creates_file(
    tmp_path,
    monkeypatch,
):

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

    # Simula a duração do vídeo.
    monkeypatch.setattr(
        TranscriptionService,
        "_get_duration",
        staticmethod(lambda source: 300.0),
    )

    # Simula a extração de um segmento.
    fake_chunk = tmp_path / "chunk_1.wav"
    fake_chunk.write_bytes(b"fake chunk")

    monkeypatch.setattr(
        TranscriptionService,
        "_extract_chunks",
        staticmethod(
            lambda source: iter([
                (
                    fake_chunk,
                    0.0,
                    300.0,
                )
            ])
        ),
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

    assert "audiencia.mp3" in content

    assert "Transcrição de teste." in content

    assert "00:00:00,000" in content


def test_transcription_emits_progress_events(
    tmp_path,
    monkeypatch,
):

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

    monkeypatch.setattr(
        TranscriptionService,
        "_get_duration",
        staticmethod(lambda source: 300.0),
    )

    fake_chunk = tmp_path / "chunk_1.wav"
    fake_chunk.write_bytes(b"fake chunk")

    monkeypatch.setattr(
        TranscriptionService,
        "_extract_chunks",
        staticmethod(
            lambda source: iter([
                (
                    fake_chunk,
                    0.0,
                    300.0,
                )
            ])
        ),
    )

    service = TranscriptionService.__new__(
        TranscriptionService
    )

    service.model = FakeModel()

    source = tmp_path / "audiencia.mp3"
    source.write_bytes(b"fake audio")

    events = []

    service.transcribe_with_progress(
        str(source),
        on_event=events.append,
    )

    event_types = [
        event["type"]
        for event in events
    ]

    assert "transcription_started" in event_types

    assert "segment_started" in event_types

    assert "text_received" in event_types

    assert "segment_completed" in event_types

    assert "transcription_completed" in event_types