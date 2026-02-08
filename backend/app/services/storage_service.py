import hashlib
import secrets
import shutil
import string
from pathlib import Path

from app.config import settings

TRACKING_CHARS = string.ascii_uppercase + string.digits


def generate_tracking_id() -> str:
    return "DOC-" + "".join(secrets.choice(TRACKING_CHARS) for _ in range(12))


def _ensure_dirs():
    for sub in ("intake", "originals", "processed"):
        (settings.storage_path / sub).mkdir(parents=True, exist_ok=True)


def compute_file_hash(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def save_original(source_path: Path, tracking_id: str, suffix: str) -> Path:
    _ensure_dirs()
    dest = settings.storage_path / "originals" / f"{tracking_id}{suffix}"
    shutil.copy2(source_path, dest)
    return dest


def get_original_path(tracking_id: str, suffix: str) -> Path:
    return settings.storage_path / "originals" / f"{tracking_id}{suffix}"


def save_uploaded_file(content: bytes, tracking_id: str, suffix: str) -> Path:
    _ensure_dirs()
    dest = settings.storage_path / "originals" / f"{tracking_id}{suffix}"
    dest.write_bytes(content)
    return dest


def compute_hash_from_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
