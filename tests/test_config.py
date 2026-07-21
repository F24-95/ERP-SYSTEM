import os
from dotenv import load_dotenv

load_dotenv()


def test_environment_variables_exist():
    assert os.getenv("DATABASE_URL") is not None, "DATABASE_URL must be set"
    assert os.getenv("SECRET_KEY") is not None, "SECRET_KEY must be set"
    assert os.getenv("ALGORITHM") is not None, "ALGORITHM must be set"


def test_secret_key_length():
    key = os.getenv("SECRET_KEY", "")
    assert len(key) >= 32, f"SECRET_KEY too short: {len(key)} chars"


def test_jwt_algorithm():
    alg = os.getenv("ALGORITHM", "HS256")
    assert alg in ("HS256", "HS384", "HS512"), f"Unsupported algorithm: {alg}"


def test_database_url_format():
    url = os.getenv("DATABASE_URL", "")
    assert url.startswith("postgresql"), (
        f"DATABASE_URL must be postgresql, got: {url[:20]}"
    )
    assert "@" in url, "DATABASE_URL must contain credentials"
