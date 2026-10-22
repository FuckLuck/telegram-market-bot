import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    bot_token: str
    channel_id: str
    db_name: str = "bot.db"


def load_config() -> Config:
    token = os.getenv("BOT_TOKEN", "").strip()
    channel = os.getenv("CHANNEL_ID", "").strip()
    db_name = os.getenv("DB_NAME", "bot.db").strip()

    return Config(
        bot_token=token,
        channel_id=channel,
        db_name=db_name,
    )
