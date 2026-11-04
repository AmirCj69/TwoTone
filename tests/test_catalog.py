"""Tests for emotion, need, and reaction catalogs."""
from bot.constants.emotions import (
    EMOTION_CATEGORIES,
    NEEDS_CATALOG,
    QUICK_REACTIONS,
    find_emotion_label,
    find_need_label,
    find_reaction_label,
)


def test_catalog_structure():
    assert "vulnerable" in EMOTION_CATEGORIES
    assert "affection" in EMOTION_CATEGORIES
    assert "heavy" in EMOTION_CATEGORIES
    assert "comfort" in EMOTION_CATEGORIES

    for cat_key, cat_data in EMOTION_CATEGORIES.items():
        assert "label" in cat_data
        assert "items" in cat_data
        assert len(cat_data["items"]) > 0

    assert len(NEEDS_CATALOG) >= 5
    assert len(QUICK_REACTIONS) >= 4


def test_label_lookup():
    assert "Unseen" in find_emotion_label("unseen")
    assert "hug" in find_need_label("hug_later").lower()
    assert "hear you" in find_reaction_label("ack_hear")
    # Fallback when key is unknown
    assert find_emotion_label("custom_unknown") == "custom_unknown"
