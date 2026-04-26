import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from src.main import app
from src.db.base import Base
from src.db.session import get_db

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_brainmap.db"

engine = create_async_engine(TEST_DATABASE_URL, echo=False, future=True)
TestingSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_create_brainmap(client: AsyncClient):
    resp = await client.post("/api/v1/brainmaps", json={
        "brainmap_id": "test-map-1",
        "title": "Test BrainMap",
        "description": "A test map",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["brainmap_id"] == "test-map-1"
    assert "root_node_id" in data


@pytest.mark.asyncio
async def test_create_and_get_node(client: AsyncClient):
    # create node
    resp = await client.post("/api/v1/brainmaps/test-map-1/nodes", json={
        "brainmap_id": "test-map-1",
        "label": "Node A",
        "content": "Content of A",
        "node_type": "concept",
        "pos_x": 10.0,
        "pos_y": 20.0,
        "pos_z": 30.0,
        "size": 2.0,
        "color": "#FF0000",
    })
    assert resp.status_code == 201
    node = resp.json()
    assert node["label"] == "Node A"
    assert node["pos_x"] == 10.0
    assert node["pos_z"] == 30.0

    # get node
    resp2 = await client.get(f"/api/v1/brainmaps/nodes/{node['id']}")
    assert resp2.status_code == 200


@pytest.mark.asyncio
async def test_spatial_search(client: AsyncClient):
    resp = await client.get("/api/v1/brainmaps/test-map-1/spatial-search", params={
        "x": 0, "y": 0, "z": 0, "radius": 50.0,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
