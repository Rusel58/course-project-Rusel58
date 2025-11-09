# ---------- Builder ----------
FROM python:3.12-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /opt/build

# ставим только прод-зависимости в venv
COPY requirements.txt .
RUN python -m venv /opt/venv \
 && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# ---------- Tester: ----------
FROM builder AS tester

WORKDIR /opt/build
COPY requirements-dev.txt .
RUN /opt/venv/bin/pip install --no-cache-dir -r requirements-dev.txt

# тесты и конфиги
COPY tests tests
COPY app app
COPY pyproject.toml pytest.ini ./
ENV PATH="/opt/venv/bin:$PATH"
RUN pytest -q

# ---------- Runtime: ----------
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    UPLOAD_DIR="/var/app/uploads"

# нужен curl только для healthcheck
HEALTHCHECK --interval=20s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import sys,urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2); sys.exit(0)" || exit 1

# непривилегированный пользователь
RUN groupadd -g 10001 appuser && \
    useradd -u 10001 -g 10001 -s /usr/sbin/nologin -m appuser

WORKDIR /app

# переносим ТОЛЬКО venv с runtime-пакетами
COPY --from=builder /opt/venv /opt/venv

# переносим код (минимум лишнего)
COPY app ./app
COPY pyproject.toml pytest.ini ./

# каталоги данных + права
RUN mkdir -p /var/app/uploads && chown -R appuser:appuser /var/app /app

USER appuser

EXPOSE 8000

# запуск uvicorn через фабрику приложения
CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
