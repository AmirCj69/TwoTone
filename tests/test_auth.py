"""Tests for configuration and authorization logic."""
import pytest
from bot.config import Config


def test_config_authorization():
    cfg = Config(
        bot_token="fake:token",
        user_a_id=1001,
        user_a_name="Alice",
        user_b_id=2002,
        user_b_name="Bob",
    )

    assert cfg.is_authorized(1001) is True
    assert cfg.is_authorized(2002) is True
    assert cfg.is_authorized(9999) is False
    assert cfg.is_authorized(0) is False

    # Alice sending to Bob
    partner_id, sender_name, partner_name = cfg.get_partner_info(1001)
    assert partner_id == 2002
    assert sender_name == "Alice"
    assert partner_name == "Bob"

    # Bob sending to Alice
    partner_id, sender_name, partner_name = cfg.get_partner_info(2002)
    assert partner_id == 1001
    assert sender_name == "Bob"
    assert partner_name == "Alice"

    # Unauthorized
    with pytest.raises(PermissionError):
        cfg.get_partner_info(9999)
