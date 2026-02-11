"""API client for expenses backend."""
import httpx
import logging
from config import settings

logger = logging.getLogger(__name__)


class APIClient:
    """HTTP client for expenses API."""

    def __init__(self):
        self.base_url = settings.api_base_url
        self.headers = {"X-API-Key": settings.api_key}

    async def create_user(self, telegram_id: int, username: str | None, 
                         first_name: str, last_name: str | None) -> dict:
        """Create a new user."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/users/",
                json={
                    "telegram_id": telegram_id,
                    "username": username,
                    "first_name": first_name,
                    "last_name": last_name,
                },
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json()

    async def update_user(self, user_id: int, username: str | None,
                         first_name: str | None, last_name: str | None) -> dict:
        """Update user information."""
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{self.base_url}/users/{user_id}",
                json={
                    "username": username,
                    "first_name": first_name,
                    "last_name": last_name,
                },
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json()

    async def get_user(self, telegram_id: int) -> httpx.Response:
        """Get user by ID."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/users/{telegram_id}",
                headers=self.headers,
            )
            return response

    async def create_category(self, title: str, telegram_id: int) -> httpx.Response:
        """Create a new category."""
        async with httpx.AsyncClient() as client:
            user_response = await self.get_user(telegram_id)
            user_data = user_response.json()
            user_id = user_data.get("id")
            response = await client.post(
                f"{self.base_url}/categories/",
                json={
                    "title": title,
                    "user_id": user_id,
                },
                headers=self.headers,
            )
            logger.info(f"Category creation response: status={response.status_code}, user_id={user_id}, title={title}")
            return response

    async def get_categories(self, telegram_id: int, page: int = 1, per_page: int = 6) -> httpx.Response:
        """Get categories for user with pagination."""
        async with httpx.AsyncClient() as client:
            user_response = await self.get_user(telegram_id)
            user_data = user_response.json()
            user_id = user_data.get("id")
            
            response = await client.get(
                f"{self.base_url}/categories/",
                params={
                    "user_id": user_id,
                    "page": page,
                    "per_page": per_page,
                },
                headers=self.headers,
            )
            logger.info(f"Get categories response: status={response.status_code}, user_id={user_id}, page={page}")
            return response

    async def update_category(self, category_id: int, title: str) -> httpx.Response:
        """Update category title."""
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{self.base_url}/categories/",
                params={"category_id": category_id},
                json={"title": title},
                headers=self.headers,
            )
            logger.info(f"Update category response: status={response.status_code}, category_id={category_id}")
            return response

    async def delete_category(self, category_id: int) -> httpx.Response:
        """Delete (disable) category."""
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.base_url}/categories/",
                params={"category_id": category_id},
                headers=self.headers,
            )
            logger.info(f"Delete category response: status={response.status_code}, category_id={category_id}")
            return response



api_client = APIClient()
