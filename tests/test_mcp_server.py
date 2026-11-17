from pathlib import Path
import re

import pytest

import transcriber.mcp_server as mcp_server
from transcriber.mcp_server import get_transcription_status, transcribe_media


def test_transcribe_media_accepts_absolute_path_with_spaces(
    tmp_path,
    monkeypatch,
):
    source = tmp_path / "reunião 01.mp4"
    source.write_bytes(b"media")
    output = tmp_path / "transcription.txt"
    output.write_text("texto transcrito", encoding="utf-8")
    calls = []

    class DeferredExecutor:
        def __init__(self):
            self.job = None

        def submit(self, function, *args):
            self.job = (function, args)

        def run(self):
            function, args = self.job
            function(*args)

    class FakeService:
        def transcribe_with_progress(
            self,
            file_path: str,
            on_event,
        ) -> Path:
            calls.append(file_path)
            on_event({"type": "transcription_started", "total_chunks": 1})
            on_event(
                {
                    "type": "segment_started",
                    "segment": 1,
                    "total_segments": 1,
                }
            )
            on_event({"type": "segment_completed", "progress": 100})
            return output

    executor = DeferredExecutor()
    monkeypatch.setattr(mcp_server, "_tasks", {})
    monkeypatch.setattr(mcp_server, "_executor", executor)
    monkeypatch.setattr(
        "transcriber.mcp_server.TranscriptionService",
        FakeService,
    )

    result = transcribe_media(str(source))
    task_id = re.search(r"ID: ([0-9a-f]{32})", result).group(1)

    assert get_transcription_status(task_id).startswith("Status: queued")
    executor.run()
    assert calls == [str(source.resolve())]
    status = get_transcription_status(task_id)
    assert str(output) in status
    assert "texto transcrito" in status


@pytest.mark.parametrize(
    ("file_path", "message"),
    [
        ("relative.mp4", "caminho absoluto"),
    ],
)
def test_transcribe_media_rejects_invalid_paths(file_path, message):
    with pytest.raises(ValueError, match=message):
        transcribe_media(file_path)


def test_transcribe_media_reports_missing_absolute_path(tmp_path):
    source = tmp_path / "missing.mp4"

    with pytest.raises(FileNotFoundError, match="encontrar o arquivo"):
        transcribe_media(str(source))


def test_transcribe_media_rejects_non_media_file(tmp_path):
    source = tmp_path / "secrets.txt"
    source.write_text("not media", encoding="utf-8")

    with pytest.raises(ValueError, match="Formato não suportado"):
        transcribe_media(str(source))
