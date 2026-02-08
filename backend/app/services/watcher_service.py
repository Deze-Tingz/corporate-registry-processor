"""Filesystem watcher for intake directory.

Monitors storage/intake/ for new files and auto-ingests them.
Run as a standalone process: python -m app.services.watcher_service
"""

import asyncio
import logging
import mimetypes
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from app.config import settings

logger = logging.getLogger(__name__)


class IntakeHandler(FileSystemEventHandler):
    def __init__(self):
        self.loop = asyncio.new_event_loop()

    def on_created(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        mime = mimetypes.guess_type(path.name)[0] or ""
        if mime not in settings.allowed_mime_types:
            logger.info("Skipping non-allowed file: %s (%s)", path.name, mime)
            return
        logger.info("New file detected: %s", path.name)
        self.loop.run_until_complete(self._ingest(path, mime))

    async def _ingest(self, path: Path, mime: str):
        from app.database import async_session
        from app.models.document import Document
        from app.services.ocr_service import extract_text
        from app.services.storage_service import (
            compute_file_hash,
            generate_tracking_id,
            save_original,
        )

        tracking_id = generate_tracking_id()
        file_hash = compute_file_hash(path)
        file_size = path.stat().st_size
        saved_path = save_original(path, tracking_id, path.suffix)
        extracted = extract_text(saved_path, mime)

        async with async_session() as db:
            doc = Document(
                tracking_id=tracking_id,
                original_filename=path.name,
                original_path=str(saved_path),
                file_hash_sha256=file_hash,
                file_size_bytes=file_size,
                mime_type=mime,
                extracted_text=extracted or None,
                status="pending_classification",
                intake_method="watcher",
            )
            db.add(doc)
            await db.commit()
            logger.info("Ingested %s as %s", path.name, tracking_id)

        # Remove from intake after processing
        try:
            path.unlink()
        except OSError:
            pass


def start_watcher():
    intake_dir = settings.storage_path / "intake"
    intake_dir.mkdir(parents=True, exist_ok=True)

    handler = IntakeHandler()
    observer = Observer()
    observer.schedule(handler, str(intake_dir), recursive=False)
    observer.start()
    logger.info("Watching %s for new files...", intake_dir)

    try:
        while observer.is_alive():
            observer.join(timeout=1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    start_watcher()
