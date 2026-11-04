"""Tests for database initialization, logging, reactions, and custom feelings."""
import pytest
from bot.database import db


@pytest.fixture
def test_db_path(tmp_path):
    """Provides a temporary SQLite database path for isolated testing."""
    return str(tmp_path / "test_twotone.db")


@pytest.mark.asyncio
async def test_init_and_log_emotion(test_db_path):
    await db.init_db(test_db_path)
    log_id = await db.log_emotion(
        sender_id=111,
        recipient_id=222,
        category_key="vulnerable",
        emotion_key="unseen",
        emotion_label="Unseen / Overlooked 🌫️",
        need_key="hug_later",
        need_label="🫂 A warm hug when we see each other",
        note="Long exhausting day",
        db_path=test_db_path,
    )
    assert log_id > 0

    entry = await db.get_emotion_by_id(log_id, db_path=test_db_path)
    assert entry is not None
    assert entry["sender_id"] == 111
    assert entry["recipient_id"] == 222
    assert entry["emotion_key"] == "unseen"
    assert entry["note"] == "Long exhausting day"
    assert entry["acknowledged_at"] is None


@pytest.mark.asyncio
async def test_reaction_and_reply(test_db_path):
    await db.init_db(test_db_path)
    log_id = await db.log_emotion(
        sender_id=111,
        recipient_id=222,
        category_key="affection",
        emotion_key="missing",
        emotion_label="Missing you deeply 💭",
        need_key="no_reply",
        need_label="🕊️ No words needed",
        db_path=test_db_path,
    )

    # Set recipient message ID
    await db.set_recipient_message_id(log_id, message_id=9876, db_path=test_db_path)

    # Record reaction
    updated = await db.record_reaction(
        log_id, "ack_hug", "🫂 Sending a warm hug", db_path=test_db_path
    )
    assert updated is not None
    assert updated["reaction_key"] == "ack_hug"
    assert updated["acknowledged_at"] is not None

    # Record follow-up reply note
    replied = await db.record_reply_note(
        log_id, "I love you too sweetie", db_path=test_db_path
    )
    assert replied["reply_note"] == "I love you too sweetie"


@pytest.mark.asyncio
async def test_custom_feelings_and_history(test_db_path):
    await db.init_db(test_db_path)
    # Add custom feeling
    cf_id = await db.add_custom_feeling(
        user_id=111,
        feeling_name="Need a silly joke",
        emoji="🤪",
        db_path=test_db_path,
    )
    assert cf_id > 0

    feelings = await db.get_custom_feelings(db_path=test_db_path)
    assert len(feelings) == 1
    assert feelings[0]["feeling_name"] == "Need a silly joke"
    assert feelings[0]["emoji"] == "🤪"

    # Delete custom feeling
    deleted = await db.delete_custom_feeling(cf_id, db_path=test_db_path)
    assert deleted is True

    feelings_after = await db.get_custom_feelings(db_path=test_db_path)
    assert len(feelings_after) == 0


@pytest.mark.asyncio
async def test_stats_and_history(test_db_path):
    await db.init_db(test_db_path)
    await db.log_emotion(
        sender_id=111,
        recipient_id=222,
        category_key="vulnerable",
        emotion_key="unseen",
        emotion_label="Unseen 🌫️",
        need_key="hug_later",
        need_label="Hug",
        db_path=test_db_path,
    )
    history = await db.get_history(limit=5, db_path=test_db_path)
    assert len(history) == 1

    stats = await db.get_stats(db_path=test_db_path)
    assert stats["total_sent"] == 1
    assert stats["acknowledged"] == 0
    assert stats["categories"]["vulnerable"] == 1
