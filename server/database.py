"""MongoDB connection setup using Motor (async driver) and Beanie (ODM).

The connection URI is read from the MONGODB_URI environment variable.
Never hardcode credentials here — this code ships to production.

Local development: copy `.env.example` to `.env` and set MONGODB_URI.
"""

import os

from beanie import init_beanie
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

MONGODB_DB_NAME = os.getenv("MONGODB_DB", "ayurdiet")

_client: AsyncIOMotorClient | None = None


def get_mongodb_uri() -> str:
    """Return the MongoDB URI from the environment or raise a clear error."""
    uri = os.getenv("MONGODB_URI")
    if not uri:
        raise RuntimeError(
            "MONGODB_URI environment variable is not set. "
            "Set it in the environment or in server/.env "
            "(see server/.env.example)."
        )
    return uri


async def init_db() -> AsyncIOMotorClient:
    """Initialise the Motor client and register Beanie document models."""
    global _client

    # Imported here to avoid a circular import at module load time.
    from models import DietPlan, DietTemplate, Food, Patient, User

    uri = get_mongodb_uri()
    _client = AsyncIOMotorClient(uri)

    await init_beanie(
        database=_client[MONGODB_DB_NAME],
        document_models=[User, Patient, Food, DietTemplate, DietPlan],
    )
    return _client


async def close_db() -> None:
    """Close the Motor client connection."""
    global _client
    if _client is not None:
        _client.close()
        _client = None
