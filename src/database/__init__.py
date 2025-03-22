import os

from src.database.models.base import Base
from src.database.session_sqlite import reset_sqlite_database as reset_database

environment = os.getenv("ENVIRONMENT", "developing")

if environment == "testing":
    from src.database.session_sqlite import (
        get_sqlite_db_contextmanager as get_db_contextmanager,  # noqa: F401
        get_sqlite_db as get_db  # noqa: F401
    )
else:
    from src.database.session_postgresql import (
        get_postgresql_db_contextmanager as get_db_contextmanager,  # noqa: F401
        get_postgresql_db as get_db  # noqa: F401
    )
