# ADR-001: RFC 7807 ошибки + Correlation ID
Дата: 2025-10-15
Статус: Accepted

## Context
Нужен единый формат ошибок, не раскрывать внутренности, уметь трассировать инциденты по correlation_id. В P03 (NFR-01) это требование уже заявлено; в P04 есть риск утечки стеков/секретов в ответах API.

## Decision
- Возвращаем ошибки в формате RFC 7807: {type, title, status, detail, correlation_id}.
- Генерируем/прокидываем `X-Correlation-ID` через middleware (если пришёл от клиента — уважаем).
- Маппинг внутренних ошибок → безопасные заголовки/детали.
- В логи отправляем correlation_id.

## Consequences
+ Единый контракт и трассировка.
± Небольшая обвязка в коде.

## Links
- NFR-01 (RFC7807 + correlation_id)
- P04: R-01 “Information disclosure”, R-02 “Untraceable errors”
- tests/test_errors.py::test_rfc7807_contract
- tests/test_errors.py::test_correlation_id_echo
