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