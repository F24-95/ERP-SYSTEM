from httpx import AsyncClient, Response


def assert_ok(response: Response, status_code: int = 200):
    assert response.status_code == status_code, (
        f"Expected {status_code}, got {response.status_code}: {response.text[:500]}"
    )


def assert_created(response: Response):
    assert_ok(response, 201)


def assert_no_content(response: Response):
    assert_ok(response, 204)


def assert_bad_request(response: Response):
    assert_ok(response, 400)


def assert_unauthorized(response: Response):
    assert_ok(response, 401)


def assert_forbidden(response: Response):
    assert_ok(response, 403)


def assert_not_found(response: Response):
    assert_ok(response, 404)


def assert_conflict(response: Response):
    assert_ok(response, 409)


def assert_unprocessable(response: Response):
    assert_ok(response, 422)


async def login(client: AsyncClient, email: str, password: str) -> dict:
    response = await client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert_ok(response)
    data = response.json()
    assert "access_token" in data
    return data


async def get_auth_headers(
    client: AsyncClient, email: str, password: str
) -> dict[str, str]:
    data = await login(client, email, password)
    return {"Authorization": f"Bearer {data['access_token']}"}
