import uuid
from contextvars import ContextVar

correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default=None)


def generate_correlation_id() -> str:
    return str(uuid.uuid4())


def set_correlation_id(correlation_id: str):
    correlation_id_var.set(correlation_id)


def get_correlation_id() -> str:
    return correlation_id_var.get()


def ensure_correlation_id(existing: str | None = None) -> str:
    cid = existing or generate_correlation_id()
    set_correlation_id(cid)
    return cid