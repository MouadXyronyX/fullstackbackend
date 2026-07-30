import logging
import httpx
from typing import Any, Optional, Union
from app.core.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

SUPABASE_URL = settings.supabase_url
SUPABASE_SERVICE_KEY = settings.supabase_service_key
SUPABASE_ANON_KEY = settings.supabase_anon_key


def _table_name(table) -> str:
    return table.__tablename__ if not isinstance(table, str) else table


class SupabaseClient:
    def __init__(self):
        self.base_url = f"{SUPABASE_URL}/rest/v1"
        self.service_headers = {
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self._client = httpx.Client(base_url=self.base_url, headers=self.service_headers)

    def select(
        self, table, columns: str = "*",
        filters: Optional[dict] = None,
        order: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> list:
        table_name = _table_name(table)
        params = {"select": columns}
        if order:
            params["order"] = order
        if limit is not None:
            params["limit"] = str(limit)
        if offset is not None:
            params["offset"] = str(offset)
        if filters:
            for key, value in self._build_filter_items(filters).items():
                params[key] = value
        url = f"/{table_name}"
        resp = self._client.get(url, params=params, headers={
            **self.service_headers,
        })
        resp.raise_for_status()
        return resp.json()

    def get_by_id(self, table, id_value: Any, id_field: str = "id",
                  columns: str = "*") -> Optional[dict]:
        results = self.select(table, columns=columns, filters={id_field: f"eq.{id_value}"}, limit=1)
        return results[0] if results else None

    def get_one(self, table, filters: dict, columns: str = "*") -> Optional[dict]:
        results = self.select(table, columns=columns, filters=filters, limit=1)
        return results[0] if results else None

    def insert(self, table, data: Union[dict, list], returning: bool = True) -> Optional[Any]:
        table_name = _table_name(table)
        is_list = isinstance(data, list)
        json_data = data if is_list else data
        headers = {**self.service_headers}
        if returning:
            headers["Prefer"] = "return=representation"
        resp = self._client.post(f"/{table_name}", json=json_data, headers=headers)
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError:
            logger.error(f"Supabase insert error {resp.status_code} on {table_name}: {resp.text}")
            logger.error(f"Data: {json_data}")
            raise
        result = resp.json()
        if is_list:
            return result
        return result[0] if result else None

    def update(self, table, id_value: Any, data: dict,
               id_field: str = "id") -> Optional[dict]:
        table_name = _table_name(table)
        headers = {**self.service_headers, "Prefer": "return=representation"}
        resp = self._client.patch(
            f"/{table_name}?{id_field}=eq.{id_value}",
            json=data, headers=headers,
        )
        resp.raise_for_status()
        result = resp.json()
        return result[0] if result else None

    def update_many(self, table, filters: dict, data: dict) -> list:
        table_name = _table_name(table)
        headers = {**self.service_headers, "Prefer": "return=representation"}
        filter_items = self._build_filter_items(filters)
        filter_str = "&".join(f"{k}={v}" for k, v in filter_items.items())
        url = f"/{table_name}?{filter_str}" if filter_str else f"/{table_name}"
        resp = self._client.patch(url, json=data, headers=headers)
        resp.raise_for_status()
        return resp.json()

    def delete(self, table, id_value: Any, id_field: str = "id") -> None:
        table_name = _table_name(table)
        resp = self._client.delete(
            f"/{table_name}?{id_field}=eq.{id_value}",
            headers=self.service_headers,
        )
        resp.raise_for_status()

    def delete_many(self, table, filters: dict) -> None:
        table_name = _table_name(table)
        filter_items = self._build_filter_items(filters)
        filter_str = "&".join(f"{k}={v}" for k, v in filter_items.items())
        url = f"/{table_name}?{filter_str}" if filter_str else f"/{table_name}"
        resp = self._client.delete(url, headers=self.service_headers)
        resp.raise_for_status()

    def count(self, table, filters: Optional[dict] = None) -> int:
        results = self.select(table, columns="id", filters=filters)
        return len(results)

    def sum(self, table, column: str, filters: Optional[dict] = None) -> float:
        results = self.select(table, columns=column, filters=filters)
        return sum(r.get(column, 0) or 0 for r in results)

    def _build_filter_items(self, filters: dict) -> dict:
        items = {}
        for key, value in filters.items():
            if isinstance(value, str) and any(
                value.startswith(p) for p in
                ["eq.", "neq.", "gt.", "gte.", "lt.", "lte.",
                 "like.", "ilike.", "in.", "is.", "not.", "cs."]
            ):
                items[key] = value
            elif isinstance(value, bool):
                items[key] = f"eq.{str(value).lower()}"
            else:
                items[key] = f"eq.{value}"
        return items

    def close(self):
        self._client.close()


_client_instance: Optional[SupabaseClient] = None


def get_supabase_client() -> SupabaseClient:
    global _client_instance
    if _client_instance is None:
        _client_instance = SupabaseClient()
    return _client_instance


def close_supabase():
    global _client_instance
    if _client_instance:
        _client_instance.close()
        _client_instance = None
