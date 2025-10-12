```markdown
# STRIDE — Угрозы и контроли

Связь с NFR из P03 (примеры: NFR-01 RFC7807, NFR-03 Log PII mask, NFR-04 Data Consistency, NFR-05 CI SCA, NFR-06 DB Migrations dry-run, NFR-07 Pagination limits, NFR-08 Rate limiting, NFR-09 Auth/ZK, NFR-12 Perf/Load).

| Узел/Поток | Угроза (STRIDE) | Риск/Описание | Контроли/Меры | NFR refs | Проверка/Доказ-во | Приоритет |
|---|---|---|---|---|---|---|
| F1 (Client→Edge) | Spoofing | Кража/подмена токенов | TLS1.2+, HSTS, JWT с коротким TTL, refresh, secure cookies, CORS | NFR-09 | e2e tests, security headers check (OWASP ZAP baseline) | High |
| F1/F2 | Tampering | Подмена тела запроса | JSON schema валидация, Pydantic validators, idempotency keys | NFR-01,NFR-09 | pytest + negative cases; ruff/linters | High |
| F2 (Edge→Core) | Repudiation | Отсутствие трассируемости | Correlation-ID, RFC7807 c trace_id, audit logs | NFR-01,NFR-03 | unit/middleware tests; logs check | Medium |
| F3 (Core→PG) | Information Disclosure | Утечка PII из ошибок/логов | Маскирование PII в логах, строгие SELECT, лишние поля не отдавать | NFR-03,NFR-04 | log redaction test; contract tests | High |
| F3 | Elevation of Privilege | SQL-инъекции, расширение прав | ORM параметризация, Least Privilege в БД, миграции с ревью | NFR-06 | SQLi tests (ZAP), DB role policy | High |
| F4 (Core↔Redis) | Tampering | Подмена кеша | Namespacing, TTL, подписи (если нужно), ограничение команд Redis | NFR-04 | integ tests; redis conf review | Medium |
| F5/F12 (/metrics) | Information Disclosure | Метрики раскрывают PII/секреты | /metrics без PII, защита по IP, отдельный порт | NFR-03 | manual check; scrape allowlist | Medium |
| F7/F8 (Admin) | Spoofing/EoP | Несанкц. доступ в админку | RBAC, 2FA/MFA, IP allowlist, отдельный audience в JWT | NFR-09 | auth tests; policy as code | High |
| F1/F2 | DoS | Флуд/Bruteforce | Rate limiting, backoff, глобальные лимиты на IP/user | NFR-08,NFR-12 | k6/gatling профили, ZAP baseline | High |
| F6 (CI hooks) | Tampering | Злонамеренные артефакты/скрипты | Pin версий, SCA/Dependabot, Verify signatures | NFR-05 | CI logs, SCA report | Medium |
| F9/F10 (Worker) | Repudiation | Нет аудита фоновых правок | Audit trail для задач, подпись job-id/actor | NFR-01 | worker logs, unit | Medium |
| Все | Information Disclosure | Ошибки без RFC7807, утечки стэктрейсов | Единый конверт ошибок, обрезка стэков в проде | NFR-01 | contract tests | High |

**Примечания**
- **Non-applicable** STRIDE для отдельных узлов помечаем и обосновываем в код-ревью (например, физические каналы).
- Угроз покрыто ≥12, потоки/элементы связаны с DFD F1…F12.
