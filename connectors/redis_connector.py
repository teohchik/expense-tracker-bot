import logging

import redis.asyncio as redis


class RedisManager:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.redis = None

    async def connect(self):
        logging.info(f"Connecting to Redis server {self.host}:{self.port}")
        self.redis = await redis.Redis(host=self.host, port=self.port)
        logging.info(f"Successfully connected to Redis server {self.host}:{self.port}")

    async def disconnect(self):
        if self.redis:
            await self.redis.aclose()
