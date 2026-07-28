"""Database service — Supabase REST API layer with CRUD utilities."""
from typing import Any, Optional, TypeVar, Generic
from pydantic import BaseModel
from app.core.supabase_client import get_supabase_client, SupabaseClient

ModelT = TypeVar("ModelT", bound=BaseModel)


class SupabaseDB:
    """High-level CRUD wrapper around SupabaseClient."""

    def __init__(self):
        self.client: SupabaseClient = get_supabase_client()

    # ── Read ──────────────────────────────────────────

    def get_all(
        self, table, columns: str = "*",
        filters: Optional[dict] = None,
        order: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> list[dict]:
        return self.client.select(
            table, columns=columns, filters=filters,
            order=order, limit=limit, offset=offset,
        )

    def get_by_id(self, table, id_value: Any, id_field: str = "id", columns: str = "*") -> Optional[dict]:
        return self.client.get_by_id(table, id_value, id_field, columns)

    def get_one(self, table, filters: dict) -> Optional[dict]:
        results = self.client.select(table, filters=filters, limit=1)
        return results[0] if results else None

    def get_by_ids(self, table, ids: list, id_field: str = "id") -> list[dict]:
        if not ids:
            return []
        header_key = id_field
        from app.core.supabase_client import get_supabase_client
        client = get_supabase_client()
        table_name = table.__tablename__ if not isinstance(table, str) else table
        filter_str = f"{id_field}=in.({','.join(str(i) for i in ids)})"
        resp = client._client.get(
            f"/{table_name}?{filter_str}",
            headers={"Accept": "application/json"},
        )
        resp.raise_for_status()
        return resp.json()

    def count(self, table, filters: Optional[dict] = None) -> int:
        return self.client.count(table, filters)

    # ── Create ────────────────────────────────────────

    def insert(self, table, data: dict) -> Optional[dict]:
        return self.client.insert(table, data, returning=True)

    def insert_many(self, table, data: list[dict]) -> list[dict]:
        return self.client.insert_many(table, data)

    # ── Update ────────────────────────────────────────

    def update(self, table, id_value: Any, data: dict, id_field: str = "id") -> Optional[dict]:
        return self.client.update(table, id_value, data, id_field)

    def update_many(self, table, filters: dict, data: dict) -> list[dict]:
        return self.client.update_many(table, filters, data)

    # ── Delete ────────────────────────────────────────

    def delete(self, table, id_value: Any, id_field: str = "id") -> None:
        return self.client.delete(table, id_value, id_field)

    def delete_many(self, table, filters: dict) -> None:
        return self.client.delete_many(table, filters)

    # ── Aggregates ────────────────────────────────────

    def sum(self, table, column: str, filters: Optional[dict] = None) -> float:
        results = self.get_all(table, columns=f"{column}", filters=filters)
        return sum(r.get(column, 0) or 0 for r in results)

    # ── Auth helpers ──────────────────────────────────

    def get_user_by_email(self, email: str) -> Optional[dict]:
        return self.get_one("users", {"email": email})

    def get_user_by_phone(self, phone: str) -> Optional[dict]:
        return self.get_one("users", {"phone": phone})

    def get_user_by_id(self, user_id: int) -> Optional[dict]:
        return self.get_by_id("users", user_id)


def get_db() -> SupabaseDB:
    """FastAPI dependency — yields a SupabaseDB instance."""
    return SupabaseDB()
