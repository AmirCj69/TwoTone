"""Configuration and partner identity management."""
import os
from dataclasses import dataclass
from typing import Optional, Tuple
from dotenv import load_dotenv

# Load from .env if present
load_dotenv()


@dataclass(frozen=True)
class Config:
    """Application configuration and partner mapping."""
    bot_token: str = os.getenv("BOT_TOKEN", "").strip()
    user_a_id: int = int(os.getenv("USER_A_ID", "0"))
    user_a_name: str = os.getenv("USER_A_NAME", "Partner A").strip()
    user_b_id: int = int(os.getenv("USER_B_ID", "0"))
    user_b_name: str = os.getenv("USER_B_NAME", "Partner B").strip()
    database_path: str = os.getenv("DATABASE_PATH", "twotone.db").strip()

    def is_authorized(self, user_id: int) -> bool:
        """Check if user_id belongs to either partner."""
        if not user_id:
            return False
        return user_id in (self.user_a_id, self.user_b_id)

    def get_sender_name(self, user_id: int) -> str:
        """Get the configured name for the given user."""
        if user_id == self.user_a_id:
            return self.user_a_name
        elif user_id == self.user_b_id:
            return self.user_b_name
        return "Someone"

    def get_partner_info(self, user_id: int) -> Tuple[int, str, str]:
        """
        Get partner details.
        Returns:
            (partner_id, sender_name, partner_name)
        Raises:
            PermissionError if the user is not authorized.
        """
        if user_id == self.user_a_id:
            return self.user_b_id, self.user_a_name, self.user_b_name
        elif user_id == self.user_b_id:
            return self.user_a_id, self.user_b_name, self.user_a_name
        raise PermissionError(f"User {user_id} is not an authorized partner.")


# Global singleton instance
config = Config()
