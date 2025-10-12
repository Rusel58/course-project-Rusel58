# Risk Register — Workout Tracking API

Скала: L/I 1..5, Risk = L×I. Стратегия: Accept / Mitigate / Avoid / Transfer.

| ID | Риск (связан с) | Описание | L | I | Risk | Стратегия | Владелец | Срок | Критерии закрытия |
|---|---|---|---:|---:|---:|---|---|---|---|
| R-01 | F1,F2 — Auth | Захват токена, сессии | 3 | 5 | 15 | Mitigate | Backend | 2025-10-20 | JWT TTL≤15m, refresh flow, secure cookies; e2e auth tests |
| R-02 | F3 — SQLi | Инъекции, эскалация | 2 | 5 | 10 | Mitigate | Backend | 2025-10-18 | ORM only, no raw SQL; ZAP baseline pass; code review checklist |
| R-03 | F1,F2 — DoS | Флуд/брутфорс | 3 | 4 | 12 | Mitigate | Platform | 2025-10-22 | Rate limit @edge/core; k6 profile meets NFR-12 TPS/p95 |
| R-04 | F5,F12 — PII leak | PII в метриках/логах | 3 | 4 | 12 | Mitigate | Backend | 2025-10-19 | Log redaction in place; /metrics reviewed; no PII in audit |
| R-05 | F6 — Supply chain | Уязвимые зависимости | 3 | 4 | 12 | Mitigate | DevOps | 2025-10-17 | CI SCA enabled; failing threshold set; Dependabot active |
| R-06 | F3 — Data consistency | Потеря целостности данных | 2 | 4 | 8 | Mitigate | Backend | 2025-10-25 | FK/UNIQUE constraints; migration dry-run; consistency tests |
| R-07 | F4 — Cache poisoning | Подмена кеша | 2 | 3 | 6 | Mitigate | Backend | 2025-10-28 | Namespacing, TTL, deny risky Redis cmds; tests |
| R-08 | F7,F8 — Admin abuse | Неавторизованный админ-доступ | 2 | 5 | 10 | Mitigate | Platform | 2025-10-20 | RBAC roles, MFA, IP allowlist; admin route tests |
| R-09 | All — Error handling | Грязные ошибки/стэктрейсы | 3 | 3 | 9 | Mitigate | Backend | 2025-10-16 | RFC7807 с trace_id, prod hides stack; contract tests pass |
| R-10 | BG — Jobs audit | Неучтённые фоновые изменения | 2 | 3 | 6 | Mitigate | Backend | 2025-10-30 | Job audit trail + correlation_id; unit tests |
| R-11 | Privacy | Избыточные поля в API ответах | 3 | 3 | 9 | Mitigate | Backend | 2025-10-21 | Response whitelists, DTOs без лишнего; contract tests |
| R-12 | Perf | Деградация p95>250ms | 3 | 3 | 9 | Accept→Mitigate | Backend | 2025-11-05 | k6 сценарии, пороги NFR-12 пройдены, профилирование |

## Карта рисков (по квадрантам)
- High (≥12): R-01, R-03, R-04, R-05 — **быстрые выигрыши** приоритетны.
- Medium (8–10): R-02, R-06, R-08, R-09, R-11, R-12.
- Low (≤6): R-07, R-10.

Связь с NFR:
- R-01 → NFR-09 (Auth), NFR-01 (Errors)
- R-02 → NFR-06 (Migrations/DB policy), NFR-05 (CI SCA)
- R-03 → NFR-08 (Rate limit), NFR-12 (Perf)
- R-04 → NFR-03 (Log PII), NFR-01
- R-05 → NFR-05
- R-06 → NFR-04, NFR-06
- R-11 → NFR-04 (DTO/минимизация полей)
