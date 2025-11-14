import os
from pathlib import Path
import uuid

ALLOWED = {"image/png", "image/jpeg"}
MAX_BYTES = 5_000_000

PNG = b"\x89PNG\r\n\x1a\n"
JPEG_SOI = b"\xff\xd8"
JPEG_EOI = b"\xff\xd9"


def sniff_image_type(data: bytes) -> str | None:
    if data.startswith(PNG):
        return "image/png"
    if data.startswith(JPEG_SOI) and data.endswith(JPEG_EOI):
        return "image/jpeg"
    return None


def secure_save(base_dir: str, data: bytes) -> tuple[bool, str]:
    if len(data) > MAX_BYTES:
        return False, "too_big"

    mt = sniff_image_type(data)
    if mt not in ALLOWED:
        return False, "bad_type"

    root = Path(base_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    if root.is_symlink():
        return False, "symlink_root"

    ext = ".png" if mt == "image/png" else ".jpg"
    name = f"{uuid.uuid4()}{ext}"

    stored_path_str: str
    dir_fd = os.open(str(root), os.O_RDONLY)
    try:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        fd = os.open(name, flags, mode=0o600, dir_fd=dir_fd)
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        stored_path_str = str(root / name)
    finally:
        try:
            os.close(dir_fd)
        except OSError:
            pass

    return True, stored_path_str
