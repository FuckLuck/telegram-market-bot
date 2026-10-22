import aiosqlite
from typing import Optional, Dict, Any, List


class Database:
    def __init__(self, db_path: str = "bot.db"):
        self.db_path = db_path

    async def init(self) -> None:
        """Initializes database tables and starting sequence."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS ads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    username TEXT,
                    full_name TEXT,
                    text TEXT NOT NULL,
                    photo_id TEXT,
                    channel_message_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active'
                )
                """
            )
            # Ensure sequence starts from 1000 (first ad will be #1001)
            # Create sqlite_sequence table entry if table was just created
            await db.execute(
                """
                INSERT INTO sqlite_sequence (name, seq)
                SELECT 'ads', 1000
                WHERE NOT EXISTS (SELECT 1 FROM sqlite_sequence WHERE name = 'ads')
                """
            )
            await db.commit()

    async def create_ad(
        self,
        user_id: int,
        username: Optional[str],
        full_name: str,
        text: str,
        photo_id: Optional[str] = None,
    ) -> int:
        """Creates a new ad and returns its unique ID."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                INSERT INTO ads (user_id, username, full_name, text, photo_id)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, username, full_name, text, photo_id),
            )
            await db.commit()
            return cursor.lastrowid

    async def update_channel_message_id(
        self, ad_id: int, channel_message_id: int
    ) -> None:
        """Saves the channel message ID for the published ad."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE ads SET channel_message_id = ? WHERE id = ?",
                (channel_message_id, ad_id),
            )
            await db.commit()

    async def get_ad(self, ad_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves an ad by its ID."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM ads WHERE id = ? AND status = 'active'", (ad_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
                return None

    async def get_user_ads(self, user_id: int) -> List[Dict[str, Any]]:
        """Retrieves all active ads submitted by a specific user."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM ads WHERE user_id = ? ORDER BY id DESC", (user_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
