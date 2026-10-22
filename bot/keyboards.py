from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Returns the persistent main menu reply keyboard."""
    keyboard = [
        [
            KeyboardButton(text="📢 Продать"),
            KeyboardButton(text="🛒 Купить"),
        ],
        [
            KeyboardButton(text="📋 Мои анкеты"),
            KeyboardButton(text="ℹ️ Помощь"),
        ],
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Returns cancel button keyboard during FSM states."""
    keyboard = [
        [KeyboardButton(text="❌ Отмена")],
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )


def get_seller_contact_keyboard(
    username: str | None, user_id: int
) -> InlineKeyboardMarkup | None:
    """Returns inline keyboard with direct link to seller."""
    if username:
        # Strip leading @ if present
        clean_username = username.lstrip("@")
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="💬 Написать продавцу",
                        url=f"https://t.me/{clean_username}",
                    )
                ]
            ]
        )
    else:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="👤 Профиль продавца",
                        url=f"tg://user?id={user_id}",
                    )
                ]
            ]
        )


def get_channel_ad_keyboard(
    bot_username: str, ad_id: int
) -> InlineKeyboardMarkup:
    """Returns inline button under the channel post linking directly to the bot."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🛒 Купить / Связаться",
                    url=f"https://t.me/{bot_username}?start=ad_{ad_id}",
                )
            ]
        ]
    )
