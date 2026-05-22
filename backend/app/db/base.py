# Import model modules so Alembic can discover table metadata.
from app.models import external, generation, llm, user  # noqa: F401
from app.models.base import Base

__all__ = ["Base"]
