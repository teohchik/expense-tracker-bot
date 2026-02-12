"""API client for expenses backend."""
import httpx
import logging
from config import settings, bot_settings

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

    async def get_categories(self, telegram_id: int, page: int = 1, per_page: int = None) -> httpx.Response:
        """Get categories for user with pagination."""
        if per_page is None:
            per_page = bot_settings.CATEGORIES_PER_PAGE
            
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

    async def create_expense(self, telegram_id: int, category_id: int, amount: float, description: str = None) -> httpx.Response:
        """Create a new expense."""
        async with httpx.AsyncClient() as client:
            user_response = await self.get_user(telegram_id)
            user_data = user_response.json()
            user_id = user_data.get("id")
            
            # Build request data
            expense_data = {
                "user_id": user_id,
                "category_id": category_id,
                "amount": amount,
            }
            
            # Only add description if it's not None
            if description is not None:
                expense_data["description"] = description
            
            response = await client.post(
                f"{self.base_url}/expenses/",
                json=expense_data,
                headers=self.headers,
            )
            logger.info(f"Create expense response: status={response.status_code}, user_id={user_id}, amount={amount}")
            return response

    async def get_expenses_for_month(self, telegram_id: int, year: int, month: int, page: int = 1, per_page: int = None) -> httpx.Response:
        """Get expenses for specific month with pagination."""
        if per_page is None:
            per_page = bot_settings.EXPENSES_PER_PAGE
            
        async with httpx.AsyncClient() as client:
            user_response = await self.get_user(telegram_id)
            user_data = user_response.json()
            user_id = user_data.get("id")
            
            response = await client.get(
                f"{self.base_url}/expenses/user/{user_id}",
                params={
                    "year": year,
                    "month": month,
                    "page": page,
                    "per_page": per_page,
                },
                headers=self.headers,
            )
            logger.info(f"Get expenses response: status={response.status_code}, user_id={user_id}, year={year}, month={month}")
            return response

    async def update_expense(self, expense_id: int, amount: float = None, description: str = None) -> httpx.Response:
        """Update expense amount and/or description."""
        async with httpx.AsyncClient() as client:
            update_data = {}
            if amount is not None:
                update_data["amount"] = amount
            if description is not None:
                update_data["description"] = description
                
            response = await client.patch(
                f"{self.base_url}/expenses/",
                params={"expense_id": expense_id},
                json=update_data,
                headers=self.headers,
            )
            logger.info(f"Update expense response: status={response.status_code}, expense_id={expense_id}")
            return response

    async def delete_expense(self, expense_id: int) -> httpx.Response:
        """Delete expense."""
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.base_url}/expenses/",
                params={"expense_id": expense_id},
                headers=self.headers,
            )
            logger.info(f"Delete expense response: status={response.status_code}, expense_id={expense_id}")
            return response



api_client = APIClient()
