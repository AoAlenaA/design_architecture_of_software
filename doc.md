# Лабораторная работа №5  
**Тема:** Реализация архитектуры на основе сервисов (микросервисной архитектуры)  
**Цель работы:** Получить опыт организации взаимодействия сервисов с использованием контейнеров Docker.

---

## 1. Архитектурное решение

В рамках лабораторной работы реализована архитектура приложения на основе контейнеров Docker. В соответствии с диаграммой контейнеров были выделены и реализованы три основных контейнера:

1. **Клиентская часть (client)** — отдельный контейнер с веб-интерфейсом.  
2. **Серверная часть (api)** — отдельный контейнер с REST API, реализованным на FastAPI.  
3. **База данных (db)** — отдельный контейнер PostgreSQL.

Общая схема взаимодействия контейнеров:

**Client → API → DB**

Клиентская часть отправляет HTTP-запросы к серверной части. Серверная часть обрабатывает запросы и взаимодействует с базой данных. Все контейнеры запускаются совместно и объединяются в одно приложение с помощью Docker Compose.

---

## 2. Структура проекта

Структура проекта после реализации лабораторной работы имеет следующий вид:

```text
analytics_api/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── index.html
│   └── Dockerfile
├── tests/
│   └── test_api.py
├── .github/
│   └── workflows/
│       └── ci.yml
├── docker-compose.yml
└── .dockerignore
```

---

## 3. Реализация контейнеров

### 3.1. Контейнер клиентской части

Клиентская часть реализована в виде простой HTML-страницы, которая загружается через Nginx. На странице размещена кнопка для загрузки списка стажёров с серверной части.

Файл `frontend/Dockerfile`:

```dockerfile
FROM nginx:alpine

COPY index.html /usr/share/nginx/html/index.html

EXPOSE 80
```

Файл `frontend/index.html`:

```html
<!doctype html>
<html lang="ru">
<head>
  <meta charset="UTF-8" />
  <title>ЛР5 — клиентская часть</title>
</head>
<body>
  <h1>ЛР5 — клиентская часть</h1>
  <button id="load">Загрузить стажёров</button>
  <pre id="result"></pre>

  <script>
    document.getElementById("load").addEventListener("click", async () => {
      try {
        const response = await fetch("http://localhost:8080/api/v1/trainees");
        const data = await response.json();
        document.getElementById("result").textContent = JSON.stringify(data, null, 2);
      } catch (e) {
        document.getElementById("result").textContent = "Ошибка: " + e;
      }
    });
  </script>
</body>
</html>
```

---

### 3.2. Контейнер серверной части

Серверная часть реализована на Python с использованием FastAPI. API поддерживает операции создания, получения, обновления и удаления стажёров, а также работу с результатами обучения и метриками. Для корректного взаимодействия с клиентской частью была добавлена настройка CORS.

Файл `backend/Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

Файл `backend/requirements.txt`:

```txt
fastapi
uvicorn[standard]
pydantic[email]
```

Основной файл серверной части: `backend/main.py`.

В приложении реализован дополнительный endpoint `/health`, который используется для проверки работоспособности API в процессе CI.

---

### 3.3. Контейнер базы данных

В качестве базы данных используется PostgreSQL. Контейнер базы данных создаётся на основе готового образа `postgres:15`. Подключение и конфигурация выполняются через переменные окружения в файле `docker-compose.yml`.

---

## 4. Оркестрация контейнеров

Для совместного запуска контейнеров используется Docker Compose.

Файл `docker-compose.yml`:

```yaml
services:
  db:
    image: postgres:15
    container_name: analytics_db
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: analytics
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  api:
    build: ./backend
    container_name: analytics_api
    ports:
      - "8080:8080"
    depends_on:
      - db

  client:
    build: ./frontend
    container_name: analytics_client
    ports:
      - "3000:80"
    depends_on:
      - api

volumes:
  postgres_data:
```

Контейнеры запускаются командой:

```bash
docker compose up --build
```

После запуска приложение доступно по следующим адресам:

- клиентская часть: `http://localhost:3000`
- серверная часть (Swagger): `http://localhost:8080/docs`

---

## 5. Проверка работоспособности приложения

После запуска контейнеров была проведена проверка работоспособности приложения.

### Выполненные проверки:
1. Успешный запуск контейнеров `client`, `api`, `db`.
2. Проверка доступности Swagger-интерфейса по адресу `http://localhost:8080/docs`.
3. Создание стажёра через Postman.
4. Получение списка стажёров на клиентской странице.
5. Проверка взаимодействия клиентской и серверной части.
6. Проверка того, что серверная часть доступна для интеграционных тестов по endpoint `/health`.

По итогам проверки приложение, состоящее из взаимодействующих контейнеров, функционирует корректно.

---

## 6. Непрерывная интеграция

Для автоматической сборки проекта и проверки его работоспособности настроен CI с использованием GitHub Actions.

Файл `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [ "main", "LabWork5" ]
  pull_request:
    branches: [ "main", "LabWork5" ]

jobs:
  build-and-test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Build containers
        run: docker compose build

      - name: Start containers
        run: docker compose up -d

      - name: Wait for API
        run: |
          for i in {1..20}; do
            if curl -f http://localhost:8080/health; then
              exit 0
            fi
            sleep 3
          done
          exit 1

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install test dependencies
        run: pip install requests pytest

      - name: Run integration tests
        run: pytest tests/test_api.py

      - name: Show logs on failure
        if: failure()
        run: docker compose logs

      - name: Stop containers
        if: always()
        run: docker compose down
```

В результате CI автоматически выполняет следующие действия:
- получает код из репозитория;
- собирает docker-образы;
- запускает контейнеры;
- ожидает готовности API;
- запускает интеграционные тесты;
- завершает работу и останавливает контейнеры.

---

## 7. Интеграционные тесты

Для проверки взаимодействия сервисов были разработаны интеграционные тесты. Они проверяют доступность API и корректную работу основных операций.

Файл `tests/test_api.py`:

```python
import time
import requests

BASE_URL = "http://localhost:8080"


def wait_for_api():
    for _ in range(30):
        try:
            r = requests.get(f"{BASE_URL}/health", timeout=3)
            if r.status_code == 200:
                return
        except Exception:
            pass
        time.sleep(2)
    raise RuntimeError("API did not start in time")


def test_health():
    wait_for_api()
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_and_list_trainee():
    wait_for_api()

    create_response = requests.post(
        f"{BASE_URL}/api/v1/trainees",
        json={
            "fullName": "Test User",
            "email": "test@example.com",
            "department": "QA",
            "hireDate": "2026-02-01"
        },
        timeout=5,
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["fullName"] == "Test User"

    list_response = requests.get(f"{BASE_URL}/api/v1/trainees", timeout=5)
    assert list_response.status_code == 200
    items = list_response.json()
    assert isinstance(items, list)
    assert any(item["email"] == "test@example.com" for item in items)
```

Интеграционные тесты были включены в процесс CI и запускаются автоматически при каждом push и pull request в соответствующие ветки.

---

## 8. Файл `.dockerignore`

Для уменьшения размера контекста сборки и исключения ненужных файлов был создан файл `.dockerignore`.

Содержимое файла:

```txt
.venv
__pycache__
*.pyc
.git
.gitignore
```
