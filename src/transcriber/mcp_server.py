from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from uuid import uuid4

from mcp.server.fastmcp import FastMCP

from transcriber.service import TranscriptionService


SUPPORTED_MEDIA_EXTENSIONS = {
    ".3gp",
    ".aac",
    ".avi",
    ".flac",
    ".m4a",
    ".m4v",
    ".mkv",
    ".mov",
    ".mp3",
    ".mp4",
    ".mpeg",
    ".mpg",
    ".ogg",
    ".ts",
    ".wav",
    ".webm",
    ".wma",
}


@dataclass
class TranscriptionTask:
    status: str = "queued"
    progress: float = 0
    current_segment: int = 0
    total_segments: int = 0
    output_path: str = ""
    error: str = ""


mcp = FastMCP("Claude Audiência")
_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="transcription")
_tasks: dict[str, TranscriptionTask] = {}
_tasks_lock = Lock()


def _process_transcription(task_id: str, source: Path) -> None:
    def handle_event(event: dict) -> None:
        with _tasks_lock:
            task = _tasks[task_id]
            if event["type"] == "transcription_started":
                task.status = "processing"
                task.total_segments = event.get("total_chunks", 0)
            elif event["type"] == "segment_started":
                task.current_segment = event.get("segment", 0)
                task.total_segments = event.get("total_segments", 0)
            elif event["type"] == "segment_completed":
                task.progress = event.get("progress", task.progress)
            elif event["type"] == "transcription_completed":
                task.progress = 100

    try:
        output = TranscriptionService().transcribe_with_progress(
            str(source),
            on_event=handle_event,
        )
        with _tasks_lock:
            task = _tasks[task_id]
            task.status = "completed"
            task.progress = 100
            task.output_path = str(output)
    except Exception as error:
        with _tasks_lock:
            task = _tasks[task_id]
            task.status = "failed"
            task.error = str(error)


@mcp.tool()
def transcribe_media(file_path: str) -> str:
    """Starts local transcription in the background; the transcript is returned to Claude Desktop and may be sent to Anthropic."""
    source = Path(file_path).expanduser()

    if not source.is_absolute():
        raise ValueError("Informe o caminho absoluto do arquivo de mídia.")

    try:
        source = source.resolve(strict=True)
    except OSError as error:
        raise FileNotFoundError(
            f"Não foi possível encontrar o arquivo: {file_path}"
        ) from error

    if not source.is_file():
        raise ValueError("O caminho informado não é um arquivo.")

    if source.suffix.lower() not in SUPPORTED_MEDIA_EXTENSIONS:
        raise ValueError(
            "Formato não suportado. Informe um arquivo de áudio ou vídeo."
        )

    task_id = uuid4().hex
    with _tasks_lock:
        _tasks[task_id] = TranscriptionTask()

    _executor.submit(_process_transcription, task_id, source)
    return (
        f"Transcrição iniciada localmente. ID: {task_id}. "
        "Consulte get_transcription_status com esse ID para acompanhar "
        "o progresso e obter o texto quando terminar."
    )


@mcp.tool()
def get_transcription_status(task_id: str) -> str:
    """Checks a background transcription task and returns its transcript when complete."""
    with _tasks_lock:
        task = _tasks.get(task_id)
        if task is None:
            raise ValueError("ID de transcrição não encontrado nesta sessão.")

        snapshot = TranscriptionTask(
            status=task.status,
            progress=task.progress,
            current_segment=task.current_segment,
            total_segments=task.total_segments,
            output_path=task.output_path,
            error=task.error,
        )

    if snapshot.status == "failed":
        return f"Falha na transcrição: {snapshot.error}"
    if snapshot.status == "completed":
        transcript = Path(snapshot.output_path).read_text(encoding="utf-8")
        return (
            f"Transcrição salva localmente em: {snapshot.output_path}\n\n"
            f"{transcript}"
        )

    return (
        f"Status: {snapshot.status}; progresso: {snapshot.progress:.2f}%; "
        f"segmento {snapshot.current_segment}/{snapshot.total_segments}."
    )


def main() -> None:
    mcp.run(transport="stdio")
