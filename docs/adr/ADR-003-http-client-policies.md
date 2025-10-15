# ADR-003: Политики исходящих HTTP (timeouts, retries, backoff)
Дата: 2025-10-15
Статус: Accepted

## Context
Без таймаутов/ретраев API подвисает и дозится зависимостями. Нужны разумные таймауты и лимит ретраев с экспоненциальным backoff.

## Decision
- httpx.AsyncClient с timeout: connect=2s, read=5s, total=5s.
- MAX_RETRIES=2 (ENV), BACKOFF_BASE=0.2s (ENV), экспоненциальный backoff (0.2s, 0.4s…).
- Ретраим только на `ConnectError`/`ReadTimeout`. Иные исключения пробрасываем.

## Consequences
+ Устойчивость к кратковременным сбоям; защищаем рабочие пулы.
− Небольшие задержки при деградации.

## Links
- NFR-06 (timeouts/retries для исходящих запросов)
- P04: R-05 “Upstream DoS”, R-06 “Resource exhaustion”
- tests/test_http_client.py::test_retries_with_backoff
