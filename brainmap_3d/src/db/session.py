from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from src.core.config import settings
from src.core.logging_utils import get_logger, StepTimer

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

logger = get_logger(__name__)


async def get_db() -> AsyncSession:
    with StepTimer(logger, "DB session acquire"):
        async with AsyncSessionLocal() as session:
            try:
                yield session
            finally:
                await session.close()
