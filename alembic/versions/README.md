# Migrations

This folder was missing entirely (along with `alembic/script.py.mako`), so
`alembic revision` / `alembic upgrade head` could not run at all — there was
no way to create the schema in a real Postgres deployment.

Both are now in place. To generate the initial migration, run once
dependencies are installed and pointed at a real database:

```bash
pip install -r requirements.txt
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

`src/main.py`'s startup event calls `Base.metadata.create_all()` automatically
(controlled by the `AUTO_CREATE_TABLES` env var, default `true`) so the app
is usable immediately without running Alembic by hand. Turn this off
(`AUTO_CREATE_TABLES=false`) in any environment where Alembic migrations are
the source of truth (staging/production), to avoid the two mechanisms
fighting each other.
