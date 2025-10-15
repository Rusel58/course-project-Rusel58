# ADR-002: Безопасные загрузки (magic bytes, лимиты, пути, симлинки, UUID-имя)
Дата: 2025-10-15
Статус: Accepted

## Context
Загрузки часто приводят к DoS/Traversal/Execution. Нужно: лимит размера/времени, проверка магических байт, нормализация путей, запрет симлинков, имя файла как UUID, ограниченный allowlist MIME.

## Decision
- ALLOWLIST: image/png, image/jpeg. Сигнатуры: PNG header; JPEG SOI+EOI.
- MAX_BYTES = 5MB.
- Имя файла игнорируем, сохраняем как UUID + корректное расширение.
- `Path.resolve()` и проверка, что путь остаётся внутри корня; запрет симлинков в родительских каталогах.
- Директория из ENV `UPLOAD_DIR` (по умолчанию `./var/uploads`).

## Consequences
+ Митигируем DoS/Traversal/Type Confusion.
− Пользователь не может влиять на имя файла.

## Links
- NFR-03 (валидация входа/загрузок)
- P04: R-03 “Path traversal”, R-04 “Upload DoS”
- tests/test_uploads.py::test_rejects_big_file
- tests/test_uploads.py::test_sniffs_bad_type
- tests/test_uploads.py::test_accepts_valid_png
