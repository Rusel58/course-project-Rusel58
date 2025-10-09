# NFR_BDD — Workouts Tracking API

> Набор Gherkin-сценариев для приёмки нефункциональных требований.
> Теги указывают область (`@api`, `@db`, `@perf`, `@security`, `@logs`, `@obs`, `@ops`, `@authz`).
> Ссылки вида `Refs: WF-NFR-XX` соответствуют таблице NFR.

---

## @api @errors — Единый конверт ошибок (problem+json)
**Refs: WF-NFR-01**
```gherkin
Feature: Ошибки API возвращаются в формате problem+json

  Scenario: Валидация параметров отдаёт problem+json
    Given сервис запущен
    When клиент вызывает GET /workouts?limit=0
    Then статус ответа 400
    And заголовок "Content-Type" равен "application/problem+json"
    And тело содержит поля "type", "title", "status", "detail", "trace_id"

  Scenario: Не найден ресурс отдаёт problem+json
    When клиент вызывает GET /workouts/00000000-0000-0000-0000-000000000000
    Then статус ответа 404
    And тело в формате problem+json
    And тело содержит "correlation_id"
```

---

## @api — Ограничение выборок и пагинация
**Refs: WF-NFR-02**
```gherkin
Feature: Пагинация и ограничение выборок /workouts

  Scenario: Значение limit по умолчанию
    When клиент вызывает GET /workouts без параметров
    Then выдано не более 25 элементов

  Scenario: Превышение max limit
    When клиент вызывает GET /workouts?limit=151
    Then статус ответа 400
    And тело в формате problem+json

  Scenario: Негативные параметры пагинации
    When клиент вызывает GET /workouts?offset=-5
    Then статус ответа 400
```

---

## @perf @obs — Производительность чтения с фильтрами
**Refs: WF-NFR-03**
```gherkin
Feature: Производительность GET /workouts под учебной нагрузкой

  Scenario: p95 не превышает 180 ms при 40 RPS
    Given профиль нагрузки "read-heavy" запущен 10 минут при 40 RPS
    When собираю метрику http_request_duration_seconds для GET /workouts
    Then p95 <= 0.180 секунды
    And процент ошибок < 1%
```

---

## @db — Индексы под основные фильтры
**Refs: WF-NFR-04**
```gherkin
Feature: Использование индексов под фильтры

  Scenario: План запроса использует составной индекс по user_id, performed_at
    Given в БД есть 100k тренировок разных пользователей
    When выполняю EXPLAIN для запроса GET /workouts?user_id=me&sort=-performed_at
    Then план запроса содержит индекс "(user_id, performed_at DESC)"

  Scenario: План запроса использует индекс по exercise_id
    When выполняю EXPLAIN для фильтра exercise_id=E1
    Then план запроса содержит индекс "(user_id, exercise_id)"
```

---

## @db @data — Целостность Workout↔Set↔Exercise
**Refs: WF-NFR-05**
```gherkin
Feature: Атомарность и целостность связей тренировок

  Scenario: Частичный отказ откатывает всю операцию
    Given существует упражнение "squat"
    When отправляю POST /workouts с наборами, и на втором наборе провоцирую ошибку БД
    Then статус ответа 500 или 409
    And в таблицах нет частично созданных записей (0 «висячих» связей)

  Scenario: Property-тест на 10k операций не создаёт orphan-ссылок
    Given генератор случайных тренировок и сетов
    When выполняю 10000 операций create/update/delete
    Then число нарушений FK/UNIQUE равно 0
```

---

## @api — Идемпотентные записи тренировок
**Refs: WF-NFR-06**
```gherkin
Feature: Повторная отправка не создаёт дубликаты

  Scenario: Один и тот же Idempotency-Key
    Given заголовок "Idempotency-Key: abc-123"
    When дважды вызываю POST /workouts с одинаковым телом
    Then создана ровно одна запись
    And второй ответ имеет статус 200 или 202 и возвращает тот же ресурс
```

---

## @logs @security — Структурные логи без чувствительных полей
**Refs: WF-NFR-07**
```gherkin
Feature: Логи безопасны и содержат request_id

  Background:
    Given включено структурное логирование в JSON

  Scenario: В логах нет содержимого заметок/секретов
    When выполняю POST /workouts с полем "notes" и заголовком Authorization
    Then последние логи не содержат исходный текст "notes"
    And последние логи не содержат токенов/секретов
    And каждая запись лога содержит "request_id"
```

---

## @obs — Метрики и трассировка
**Refs: WF-NFR-08 (наблюдаемость)**
```gherkin
Feature: Метрики Prometheus и трассировка OpenTelemetry

  Scenario: endpoint /metrics доступен и содержит HTTP-гистограммы
    When клиент вызывает GET /metrics
    Then статус 200
    And тело содержит имя метрики "http_request_duration_seconds"

  Scenario: trace_id прокидывается в ответ и логи
    When клиент вызывает GET /workouts
    Then ответ содержит заголовок "Traceparent" или "X-Trace-Id"
    And в логах за это время есть запись с тем же trace_id
```

---

## @availability — Доступность чтения
**Refs: WF-NFR-09**
```gherkin
Feature: Доступность GET /workouts

  Scenario: SLI доступности за отчётный месяц
    Given собранные логи ошибок и таймаутов за месяц
    When вычисляю долю успешных запросов для GET /workouts
    Then значение >= 99.5%
```

---

## @security @ops — Аудит зависимостей (SCA)
**Refs: WF-NFR-10**
```gherkin
Feature: SCA-гейт на CI

  Scenario: Нет High/Critical уязвимостей
    When запускается job "sca-audit" на PR
    Then статус job равен success
    And список уязвимостей не содержит уровни High или Critical
```

---

## @ops @db — Миграции с dry-run
**Refs: WF-NFR-11**
```gherkin
Feature: Безопасные миграции

  Scenario: Alembic dry-run генерирует SQL
    When запускаю "alembic upgrade head --sql"
    Then команда завершается с кодом 0
    And артефакт SQL-плана опубликован в CI

  Scenario: Все изменения схемы только через миграции
    Given изменённая модель БД
    When прогоняю проверки в CI
    Then workflow падает, если есть «ручные» изменения без миграции
```

---

## @api — Стабильная сортировка и консистентная пагинация
**Refs: WF-NFR-12**
```gherkin
Feature: Детерминированная сортировка и листание страниц

  Scenario: Элемент не повторяется между страницами
    Given сортировка "-performed_at, id"
    When получаю страницы 1 и 2 с одинаковым фильтром
    Then пересечение множеств id на страницах равно пустому множеству

  Scenario: Tie-break по id
    Given две тренировки с одинаковым performed_at
    When запрашиваю список
    Then порядок определяется по возрастанию id
```

---

## @authz — Изоляция данных пользователя
**Refs: WF-NFR-13**
```gherkin
Feature: Пользователь видит только свои тренировки

  Scenario: Чтение чужого ресурса
    Given user A имеет тренировку W1, user B аутентифицирован
    When user B вызывает GET /workouts/W1
    Then статус ответа 404 или 403

  Scenario: Запись в чужой ресурс
    Given user A имеет тренировку W2, user B аутентифицирован
    When user B вызывает PUT /workouts/W2
    Then статус ответа 403
```
