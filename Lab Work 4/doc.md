# Лабораторная работа №4  
## Тема: Проектирование REST API  
**Цель:** получить опыт проектирования программного интерфейса (REST API) и его тестирования.

Проект: **ИИ‑платформа адаптации менеджеров по продажам** (аналитический модуль: прогресс, метрики, риски, отчёты).

---

## 1) Документация по API

### 1.1. Общие правила

**Base URL (пример):**
- `https://localhost:8080` (dev)
- Все методы ниже начинаются с `/api`

**Аутентификация и авторизация**
- `Authorization: Bearer <JWT>` (OIDC/OAuth2)
- Роли (пример): `SALES_HEAD`, `HR_ANALYST`, `ADMIN`
- Область видимости данных: департамент/команда (scope), проверяется на сервере.

**Формат дат**
- `YYYY-MM-DD` (ISO-8601)

**Формат ответа об ошибке (единый)**
```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "Access denied",
    "details": {
      "traineeId": "…"
    }
  }
}
```

**Типовые HTTP статусы**
- `200 OK` — успешный запрос
- `400 Bad Request` — ошибки параметров
- `401 Unauthorized` — нет/невалидный токен
- `403 Forbidden` — нет прав/не тот scope
- `404 Not Found` — сущность не найдена
- `422 Unprocessable Entity` — логически некорректный запрос (например, from > to)
- `500 Internal Server Error` — непредвиденная ошибка

**Пагинация (где применимо)**
- `page` (0..N), `size` (1..200), `sort` (например `createdAt,desc`)
- В ответе: `page`, `size`, `total`

---

## 2) Реализуемые API (для аналитического модуля)

Ниже приведён набор REST‑методов, покрывающий ключевые сценарии: отчёты, динамика метрик, риски/алерты и справочники.


---

### API-1. Отчёт по стажёру (прогресс + проблемные зоны + риск)

**Метод:** `GET`  
**URL:** `/api/reports/trainees/{traineeId}`

**Query параметры**
- `from` (required, `YYYY-MM-DD`) — начало периода
- `to` (required, `YYYY-MM-DD`) — конец периода
- `include` (optional, csv) — опциональные секции отчёта: `timeline,errors,stages`
  - пример: `include=timeline,errors`

**Headers**
- `Authorization: Bearer <JWT>`
- `Accept: application/json`

**Ответ 200 (пример)**
```json
{
  "traineeId": "8b5b7f37-0b05-4c62-9f85-9b7c7e22c2be",
  "period": { "from": "2026-02-01", "to": "2026-02-15" },
  "progressPct": 62.5,
  "avgScore": 78.2,
  "attemptsCount": 14,
  "risk": { "riskScore": 3, "level": "WARN", "reasons": ["Повторяющиеся ошибки (>=5)"] },
  "weakZones": [
    { "code": "OBJECTIONS", "title": "Работа с возражениями", "count": 6 },
    { "code": "CLOSING", "title": "Закрытие сделки", "count": 4 }
  ],
  "stageBreakdown": [
    { "stageCode": "QUALIFY", "stageTitle": "Квалификация", "errors": 2, "avgScore": 80.0 },
    { "stageCode": "PRESENT", "stageTitle": "Презентация", "errors": 3, "avgScore": 75.0 }
  ]
}
```

**Ошибки**
- `400` — отсутствует `from/to` или неверный формат
- `422` — `from > to`
- `403` — нет прав смотреть стажёра (не тот отдел/роль)
- `404` — traineeId не найден

---

### API-2. Командный отчёт (узкие места команды + распределение ошибок)

**Метод:** `GET`  
**URL:** `/api/reports/teams/{teamId}`

**Query параметры**
- `from` (required)
- `to` (required)
- `groupBy` (optional) — `stage` (по этапам воронки) или `errorType` (по типам ошибок); default `stage`

**Ответ 200 (пример)**
```json
{
  "teamId": "c4e3b0c1-4d8d-4a4e-9b42-8a2f1d4f1c11",
  "period": { "from": "2026-02-01", "to": "2026-02-15" },
  "traineesCount": 7,
  "avgProgressPct": 55.1,
  "topBottlenecks": [
    { "stageCode": "OBJECTION", "stageTitle": "Возражения", "errorSharePct": 31.0 },
    { "stageCode": "CLOSING", "stageTitle": "Закрытие", "errorSharePct": 22.0 }
  ],
  "distribution": [
    { "key": "OBJECTION", "title": "Возражения", "count": 42 },
    { "key": "CLOSING", "title": "Закрытие", "count": 30 }
  ]
}
```

---

### API-3. Динамика метрик стажёра (таймлайн прогресса/баллов)

**Метод:** `GET`  
**URL:** `/api/metrics/trainees/{traineeId}/timeline`

**Query параметры**
- `from` (required)
- `to` (required)
- `step` (optional) — `day|week`; default `day`

**Ответ 200 (пример)**
```json
{
  "traineeId": "8b5b7f37-0b05-4c62-9f85-9b7c7e22c2be",
  "period": { "from": "2026-02-01", "to": "2026-02-15" },
  "step": "day",
  "points": [
    { "date": "2026-02-01", "progressPct": 10.0, "avgScore": 65.0, "errors": 3 },
    { "date": "2026-02-02", "progressPct": 15.0, "avgScore": 70.0, "errors": 2 }
  ]
}
```

---

### API-4. Получить список риск‑алертов (для руководителя/HR)

**Метод:** `GET`  
**URL:** `/api/alerts`

**Query параметры**
- `status` (optional) — `active|closed`; default `active`
- `level` (optional) — `INFO|WARN|CRITICAL`
- `teamId` (optional) — фильтр по команде
- `page` (optional), `size` (optional), `sort` (optional)

**Ответ 200 (пример)**
```json
{
  "page": 0,
  "size": 20,
  "total": 2,
  "items": [
    {
      "alertId": "c2b55dcb-8d1a-4cb6-9b61-1e4c2b49c1a2",
      "createdAt": "2026-02-15T10:12:00Z",
      "traineeId": "8b5b7f37-0b05-4c62-9f85-9b7c7e22c2be",
      "riskType": "REPEATED_ERRORS",
      "level": "WARN",
      "reasons": ["Повторяющиеся ошибки (>=5)"],
      "isActive": true
    }
  ]
}
```

---

### API-5. Подтвердить/закрыть алерт (acknowledge)

**Метод:** `POST`  
**URL:** `/api/alerts/{alertId}/ack`

**Body (application/json)**
```json
{
  "comment": "Провёл разбор ошибок, назначил доп. тренажёр",
  "close": true
}
```

**Ответ 200 (пример)**
```json
{
  "alertId": "c2b55dcb-8d1a-4cb6-9b61-1e4c2b49c1a2",
  "isActive": false,
  "closedAt": "2026-02-15T12:00:00Z"
}
```

**Ошибки**
- `403` — нет прав закрывать алерты
- `404` — alertId не найден

---

### API-6. Справочники (типы ошибок, этапы воронки)

#### 6.1 Типы ошибок
**Метод:** `GET`  
**URL:** `/api/dictionaries/error-types`

**Ответ 200 (пример)**
```json
{
  "items": [
    { "code": "SKIP_STAGE", "title": "Пропуск этапов воронки", "severity": 3 },
    { "code": "PRODUCT_KNOWLEDGE", "title": "Слабое знание продукта", "severity": 2 },
    { "code": "OBJECTIONS", "title": "Ошибки в работе с возражениями", "severity": 3 },
    { "code": "CLOSING", "title": "Проблемы с закрытием сделки", "severity": 3 }
  ]
}
```

#### 6.2 Этапы воронки
**Метод:** `GET`  
**URL:** `/api/dictionaries/funnel-stages`

**Ответ 200 (пример)**
```json
{
  "items": [
    { "code": "QUALIFY", "title": "Квалификация", "order": 1 },
    { "code": "NEEDS", "title": "Выявление потребностей", "order": 2 },
    { "code": "PRESENT", "title": "Презентация", "order": 3 },
    { "code": "OBJECTION", "title": "Возражения", "order": 4 },
    { "code": "CLOSING", "title": "Закрытие", "order": 5 }
  ]
}
```

---

## 3) Тестирование API (Postman + автотесты)


### Тесты для API-1: GET /api/reports/trainees/{traineeId}

**Тестируемое API:** Отчёт по стажёру  
**Метод:** GET  
**Строка запроса (пример):**
```
{{baseUrl}}/api/reports/trainees/{{traineeId}}?from=2026-02-01&to=2026-02-15&include=timeline,errors
```

**Postman (что показать скриншотами):**
- Params: `from`, `to`, `include`
- Authorization: Bearer Token = `{{token}}`
- Headers: `Accept: application/json`
- Response Body + Response Headers
- Test Results

**Postman Tests (JS):**
```javascript
pm.test("Status is 200", function () {
  pm.response.to.have.status(200);
});

pm.test("Has required fields", function () {
  const json = pm.response.json();
  pm.expect(json).to.have.property("traineeId");
  pm.expect(json).to.have.property("progressPct");
  pm.expect(json).to.have.property("avgScore");
  pm.expect(json).to.have.property("risk");
});

pm.test("Progress in [0..100]", function () {
  const json = pm.response.json();
  pm.expect(json.progressPct).to.be.at.least(0);
  pm.expect(json.progressPct).to.be.at.most(100);
});
```

---

### Тесты для API-2: GET /api/reports/teams/{teamId}

**Метод:** GET  
**Строка запроса (пример):**
```
{{baseUrl}}/api/reports/teams/{{teamId}}?from=2026-02-01&to=2026-02-15&groupBy=stage
```

**Postman Tests:**
```javascript
pm.test("Status is 200", () => pm.response.to.have.status(200));

pm.test("Distribution exists", () => {
  const json = pm.response.json();
  pm.expect(json).to.have.property("distribution");
  pm.expect(json.distribution).to.be.an("array");
});
```

---

### Тесты для API-3: GET /api/metrics/trainees/{traineeId}/timeline

**Метод:** GET  
**Строка запроса (пример):**
```
{{baseUrl}}/api/metrics/trainees/{{traineeId}}/timeline?from=2026-02-01&to=2026-02-15&step=day
```

**Postman Tests:**
```javascript
pm.test("Status is 200", () => pm.response.to.have.status(200));

pm.test("Points array", () => {
  const json = pm.response.json();
  pm.expect(json.points).to.be.an("array");
  if (json.points.length > 0) {
    pm.expect(json.points[0]).to.have.property("date");
  }
});
```

---

### Тесты для API-4: GET /api/alerts

**Метод:** GET  
**Строка запроса (пример):**
```
{{baseUrl}}/api/alerts?status=active&level=WARN&page=0&size=20&sort=createdAt,desc
```

**Postman Tests:**
```javascript
pm.test("Status is 200", () => pm.response.to.have.status(200));

pm.test("Pagination shape", () => {
  const json = pm.response.json();
  pm.expect(json).to.have.property("page");
  pm.expect(json).to.have.property("size");
  pm.expect(json).to.have.property("total");
  pm.expect(json).to.have.property("items");
});
```

---

### Тесты для API-5: POST /api/alerts/{alertId}/ack

**Метод:** POST  
**Строка запроса (пример):**
```
{{baseUrl}}/api/alerts/{{alertId}}/ack
```

**Body (raw JSON):**
```json
{
  "comment": "Провёл разбор ошибок, назначил доп. тренажёр",
  "close": true
}
```

**Postman Tests:**
```javascript
pm.test("Status is 200", () => pm.response.to.have.status(200));

pm.test("Alert is closed", () => {
  const json = pm.response.json();
  pm.expect(json).to.have.property("isActive");
  pm.expect(json.isActive).to.eql(false);
});
```

---

### Тесты для API-6: GET /api/dictionaries/error-types и /funnel-stages

**Метод:** GET  
**Строки запросов (пример):**
```
{{baseUrl}}/api/dictionaries/error-types
{{baseUrl}}/api/dictionaries/funnel-stages
```

**Postman Tests (для обоих):**
```javascript
pm.test("Status is 200", () => pm.response.to.have.status(200));

pm.test("Items array", () => {
  const json = pm.response.json();
  pm.expect(json.items).to.be.an("array");
});
```

---

## 4) Автотесты вне Postman (пример: Python + pytest)

Если преподаватель требует “код автотестов” отдельным файлом, можно приложить минимальный pytest.

**requirements.txt**
```txt
pytest
requests
```

**test_api.py**
```python
import os
import requests

BASE_URL = os.getenv("BASE_URL", "https://localhost:8080")
TOKEN = os.getenv("TOKEN", "")
TRAINEE_ID = os.getenv("TRAINEE_ID", "8b5b7f37-0b05-4c62-9f85-9b7c7e22c2be")
TEAM_ID = os.getenv("TEAM_ID", "c4e3b0c1-4d8d-4a4e-9b42-8a2f1d4f1c11")

def headers():
    return {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/json",
    }

def test_trainee_report_status_and_fields():
    url = f"{BASE_URL}/api/reports/trainees/{TRAINEE_ID}"
    r = requests.get(url, params={"from": "2026-02-01", "to": "2026-02-15"}, headers=headers(), verify=False)
    assert r.status_code == 200
    js = r.json()
    assert "traineeId" in js
    assert "progressPct" in js
    assert 0 <= js["progressPct"] <= 100

def test_team_report_distribution():
    url = f"{BASE_URL}/api/reports/teams/{TEAM_ID}"
    r = requests.get(url, params={"from": "2026-02-01", "to": "2026-02-15"}, headers=headers(), verify=False)
    assert r.status_code == 200
    js = r.json()
    assert "distribution" in js
    assert isinstance(js["distribution"], list)
```

Запуск:
```bash
BASE_URL=https://localhost:8080 TOKEN="<JWT>" pytest -q
```

> `verify=False` используется для dev‑окружения с самоподписанным сертификатом.

---


