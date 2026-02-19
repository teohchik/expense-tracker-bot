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

    async def update_user(self, user_id: int, username: str | None = None,
                         first_name: str | None = None, last_name: str | None = None,
                         currency: str | None = None) -> dict:
        """Update user information."""
        async with httpx.AsyncClient() as client:
            update_data = {}
            if username is not None:
                update_data["username"] = username
            if first_name is not None:
                update_data["first_name"] = first_name
            if last_name is not None:
                update_data["last_name"] = last_name
            if currency is not None:
                update_data["currency"] = currency
                
            response = await client.patch(
                f"{self.base_url}/users/{user_id}",
                json=update_data,
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

    async def update_user_currency(self, telegram_id: int, currency: str) -> httpx.Response:
        """Update user currency."""
        async with httpx.AsyncClient() as client:
            user_response = await self.get_user(telegram_id)
            if user_response.status_code != 200:
                return user_response
                
            user_data = user_response.json()
            user_id = user_data.get("id")
            
            response = await client.patch(
                f"{self.base_url}/users/{user_id}",
                json={"currency": currency},
                headers=self.headers,
            )
            logger.info(f"Update user currency response: status={response.status_code}, user_id={user_id}, telegram_id={telegram_id}, currency={currency}")
            return response

    async def create_salary(self, telegram_id: int, amount: float, description: str = None) -> httpx.Response:
        """Create a new salary entry."""
        async with httpx.AsyncClient() as client:
            user_response = await self.get_user(telegram_id)
            user_data = user_response.json()
            user_id = user_data.get("id")

            salary_data: dict = {"user_id": user_id, "amount": amount}
            if description is not None:
                salary_data["description"] = description

            response = await client.post(
                f"{self.base_url}/salaries/",
                json=salary_data,
                headers=self.headers,
            )
            logger.info(f"Create salary response: status={response.status_code}, user_id={user_id}, amount={amount}")
            return response

    async def get_salaries_for_month(self, telegram_id: int, year: int, month: int, page: int = 1, per_page: int = None) -> httpx.Response:
        """Get salaries for specific month with pagination."""
        if per_page is None:
            per_page = bot_settings.EXPENSES_PER_PAGE

        async with httpx.AsyncClient() as client:
            user_response = await self.get_user(telegram_id)
            user_data = user_response.json()
            user_id = user_data.get("id")

            response = await client.get(
                f"{self.base_url}/salaries/user/{user_id}",
                params={"year": year, "month": month, "page": page, "per_page": per_page},
                headers=self.headers,
            )
            logger.info(f"Get salaries response: status={response.status_code}, user_id={user_id}, year={year}, month={month}")
            return response

    async def update_salary(self, salary_id: int, amount: float = None, description: str = None) -> httpx.Response:
        """Update salary amount and/or description."""
        async with httpx.AsyncClient() as client:
            update_data = {}
            if amount is not None:
                update_data["amount"] = amount
            if description is not None:
                update_data["description"] = description

            response = await client.patch(
                f"{self.base_url}/salaries/",
                params={"salary_id": salary_id},
                json=update_data,
                headers=self.headers,
            )
            logger.info(f"Update salary response: status={response.status_code}, salary_id={salary_id}")
            return response

    async def delete_salary(self, salary_id: int) -> httpx.Response:
        """Delete salary."""
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.base_url}/salaries/",
                params={"salary_id": salary_id},
                headers=self.headers,
            )
            logger.info(f"Delete salary response: status={response.status_code}, salary_id={salary_id}")
            return response

    async def get_all_users(self) -> list[dict]:
        """Get all users from the API with pagination.
        
        Returns:
            List of all user dictionaries
        """
        all_users = []
        page = 1
        per_page = 100
        
        async with httpx.AsyncClient() as client:
            while True:
                response = await client.get(
                    f"{self.base_url}/users/",
                    params={
                        "page": page,
                        "per_page": per_page,
                    },
                    headers=self.headers,
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to get users: status={response.status_code}, page={page}")
                    break
                
                users = response.json()
                if not users:
                    break
                
                all_users.extend(users)
                
                # If we got fewer users than per_page, we're on the last page
                if len(users) < per_page:
                    break
                
                page += 1
        
        logger.info(f"Retrieved {len(all_users)} total users")
        return all_users


api_client = APIClient()
