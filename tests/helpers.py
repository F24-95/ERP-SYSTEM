from typing import Dict, Optional
from httpx import AsyncClient


async def auth_header(client: AsyncClient, email: str, password: str) -> Dict[str, str]:
    response = await client.post(
        "/auth/login", json={"email": email, "password": password}
    )
    assert response.status_code == 200, f"Login failed for {email}: {response.text}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def assert_success_response(response, status_code: int = 200):
    assert response.status_code == status_code, (
        f"Expected {status_code}, got {response.status_code}: {response.text}"
    )


def assert_error_response(response, status_code: int, error_code: Optional[str] = None):
    assert response.status_code == status_code, (
        f"Expected {status_code}, got {response.status_code}: {response.text}"
    )
    data = response.json()
    assert "error" in data or "detail" in data, f"No error in response: {data}"
    if error_code and "error" in data:
        assert data["error"].get("code") == error_code, (
            f"Expected error code {error_code}, got {data['error'].get('code')}"
        )


VALID_ADMIN_LOGIN = {"email": "admin@test.com", "password": "Admin123!"}
VALID_TEACHER_LOGIN = {"email": "teacher@test.com", "password": "Teacher123!"}
VALID_STUDENT_LOGIN = {"email": "student@test.com", "password": "Student123!"}

INVALID_TOKENS = [
    "",
    "Bearer",
    "Bearer ",
    "Bearer invalid_token_here",
    "Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.invalid",
    "Basic dGVzdDpwYXNz",
]

INVALID_EMAILS = [
    "notanemail",
    "",
    "   ",
    "@domain.com",
    "user@",
    "a" * 300 + "@test.com",
]

INVALID_PHONES = ["", "123", "abcdefghij", "999999999", "99999999999"]

INVALID_IDS = [0, -1, 999999, 1.5, "abc"]

SQL_INJECTION_PAYLOADS = [
    "' OR '1'='1",
    "'; DROP TABLE users; --",
    "' UNION SELECT * FROM users; --",
    "1; SELECT * FROM users",
    "' OR 1=1 --",
    '" OR 1=1 --',
    "admin'--",
]

XSS_PAYLOADS = [
    "<script>alert('xss')</script>",
    "<img src=x onerror=alert(1)>",
    "javascript:alert(1)",
    "<svg onload=alert(1)>",
]

LARGE_PAYLOAD = "x" * 100000
