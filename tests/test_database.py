import pytest
import pytest_asyncio
import os
from bot.database import Database

TEST_DB = "test_bot.db"


@pytest_asyncio.fixture
async def db():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    database = Database(TEST_DB)
    await database.init()
    yield database
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


@pytest.mark.asyncio
async def test_create_and_get_ad(db):
    ad_id = await db.create_ad(
        user_id=12345678,
        username="@testuser",
        full_name="Test User",
        text="Продам iPhone 15 Pro, 256GB. Цена: 80000 руб.",
        photo_id="photo_123",
    )

    # First ID should be 1001 (due to sequence initialized at 1000)
    assert ad_id == 1001

    ad = await db.get_ad(1001)
    assert ad is not None
    assert ad["id"] == 1001
    assert ad["user_id"] == 12345678
    assert ad["username"] == "@testuser"
    assert ad["full_name"] == "Test User"
    assert "iPhone 15 Pro" in ad["text"]
    assert ad["photo_id"] == "photo_123"
    assert ad["status"] == "active"


@pytest.mark.asyncio
async def test_second_ad_increments_id(db):
    id1 = await db.create_ad(
        user_id=111,
        username="@user1",
        full_name="User One",
        text="Товар 1",
    )
    id2 = await db.create_ad(
        user_id=222,
        username="@user2",
        full_name="User Two",
        text="Товар 2",
    )

    assert id1 == 1001
    assert id2 == 1002


@pytest.mark.asyncio
async def test_get_nonexistent_ad(db):
    ad = await db.get_ad(9999)
    assert ad is None


@pytest.mark.asyncio
async def test_update_channel_message_id(db):
    ad_id = await db.create_ad(
        user_id=111,
        username="@user1",
        full_name="User One",
        text="Товар 1",
    )
    await db.update_channel_message_id(ad_id, 4567)
    ad = await db.get_ad(ad_id)
    assert ad["channel_message_id"] == 4567


@pytest.mark.asyncio
async def test_get_user_ads(db):
    await db.create_ad(user_id=100, username="@u1", full_name="U1", text="Ad 1")
    await db.create_ad(user_id=100, username="@u1", full_name="U1", text="Ad 2")
    await db.create_ad(user_id=200, username="@u2", full_name="U2", text="Ad 3")

    user_ads = await db.get_user_ads(100)
    assert len(user_ads) == 2
    assert user_ads[0]["id"] == 1002
    assert user_ads[1]["id"] == 1001
