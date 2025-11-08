import httpx
import pytest

from app.common.upload import MAX_BYTES
from app.main import create_app

PNG_HEADER = b"\x89PNG\r\n\x1a\n"
VALID_PNG = PNG_HEADER + b"0" * 100
JPEG_SOI = b"\xff\xd8"
JPEG_EOI = b"\xff\xd9"


@pytest.mark.asyncio
async def test_accepts_valid_png(tmp_path, monkeypatch):
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path))
    app = create_app()
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        files = {"file": ("ok.png", VALID_PNG, "image/png")}
        r = await ac.post("/upload/image", files=files)

    assert r.status_code == 200, r.text
    stored = r.json().get("stored_as")
    assert stored, r.text
    assert (tmp_path / stored.split("/")[-1]).exists()


@pytest.mark.asyncio
async def test_rejects_big_file(tmp_path, monkeypatch):
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path))
    app = create_app()
    transport = httpx.ASGITransport(app=app)
    payload = PNG_HEADER + b"0" * (MAX_BYTES - len(PNG_HEADER) + 1)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        files = {"file": ("big.png", payload, "image/png")}
        r = await ac.post("/upload/image", files=files)

    assert r.status_code == 400, r.text
    body = r.json()
    assert body.get("title") == "Invalid upload"
    assert body.get("status") == 400


@pytest.mark.asyncio
async def test_sniffs_bad_type(tmp_path, monkeypatch):
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path))
    app = create_app()
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        files = {"file": ("hack.txt", b"not-an-image", "text/plain")}
        r = await ac.post("/upload/image", files=files)

    assert r.status_code == 400, r.text
    body = r.json()
    assert body.get("title") == "Invalid upload"
    assert body.get("status") == 400
    assert "Unsupported" in (body.get("detail") or "") or "Invalid" in (body.get("detail") or "")


@pytest.mark.asyncio
async def test_rejects_jpeg_without_eoi(tmp_path, monkeypatch):
    """JPEG без завершающего EOI должен быть отклонён."""
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path))
    app = create_app()
    transport = httpx.ASGITransport(app=app)
    bad_jpeg = JPEG_SOI + b"0" * 128  # нет EOI

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        files = {"file": ("x.jpg", bad_jpeg, "image/jpeg")}
        r = await ac.post("/upload/image", files=files)

    assert r.status_code == 400, r.text
    body = r.json()
    assert body.get("title") == "Invalid upload"
    assert body.get("status") == 400


@pytest.mark.asyncio
async def test_accepts_exactly_max_size_png(tmp_path, monkeypatch):
    """Ровно MAX_BYTES байт — валидный граничный случай."""
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path))
    app = create_app()
    transport = httpx.ASGITransport(app=app)
    payload = PNG_HEADER + b"0" * (MAX_BYTES - len(PNG_HEADER))

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        files = {"file": ("edge.png", payload, "image/png")}
        r = await ac.post("/upload/image", files=files)

    assert r.status_code == 200, r.text
    stored = r.json().get("stored_as")
    assert stored
    assert (tmp_path / stored.split("/")[-1]).exists()
