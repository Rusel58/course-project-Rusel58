import pytest
from httpx import AsyncClient

from app.main import create_app

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 100


@pytest.mark.asyncio
async def test_accepts_valid_png(tmp_path, monkeypatch):
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path))
    app = create_app()
    async with AsyncClient(app=app, base_url="http://test") as ac:
        files = {"file": ("x.png", PNG, "image/png")}
        r = await ac.post("/upload/image", files=files)
    assert r.status_code == 200
    assert (tmp_path / r.json()["stored_as"].split("/")[-1]).exists()


@pytest.mark.asyncio
async def test_rejects_big_file(tmp_path, monkeypatch):
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path))
    app = create_app()
    big = b"\x89PNG\r\n\x1a\n" + b"0" * 5_000_001
    async with AsyncClient(app=app, base_url="http://test") as ac:
        files = {"file": ("b.png", big, "image/png")}
        r = await ac.post("/upload/image", files=files)
    assert r.status_code == 400
    body = r.json()
    assert body["title"] == "Invalid upload"
    assert body["status"] == 400


@pytest.mark.asyncio
async def test_sniffs_bad_type(tmp_path, monkeypatch):
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path))
    app = create_app()
    async with AsyncClient(app=app, base_url="http://test") as ac:
        files = {"file": ("hack.txt", b"not-an-image", "text/plain")}
        r = await ac.post("/upload/image", files=files)
    assert r.status_code == 400
    assert "Unsupported" in r.json()["detail"]
