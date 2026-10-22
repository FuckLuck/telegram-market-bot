import logging
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from bot.database import Database
from bot.config import Config
from bot.states import SellStates
from bot.keyboards import (
    get_main_keyboard,
    get_cancel_keyboard,
    get_channel_ad_keyboard,
)

logger = logging.getLogger(__name__)
router = Router()

TEMPLATE_TEXT = (
    "📋 <b>Шаблон анкеты для размещения:</b>\n\n"
    "<code>1. Товар / Услуга:\n"
    "2. Описание:\n"
    "3. Цена:\n"
    "4. Город / Способ передачи:\n"
    "5. Дополнительно:</code>\n\n"
    "✍️ <b>Скопируйте шаблон выше, заполните его и отправьте ответным сообщением.</b>\n"
    "📷 <i>Вы также можете прикрепить к сообщению фото товара!</i>"
)


@router.message(F.text == "📢 Продать")
@router.message(Command("sell"))
async def start_sell(message: Message, state: FSMContext):
    await state.set_state(SellStates.waiting_for_ad)

    warning_username = ""
    if not message.from_user.username:
        warning_username = (
            "⚠️ <b>Внимание:</b> У вас в Telegram не установлен @username (имя пользователя).\n"
            "Покупателям будет сложнее связаться с вами напрямую. "
            "Рекомендуем установить юзернейм в настройках Telegram.\n\n"
        )

    await message.answer(
        f"{warning_username}{TEMPLATE_TEXT}",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard(),
    )


@router.message(SellStates.waiting_for_ad, F.photo)
@router.message(SellStates.waiting_for_ad, F.text)
async def process_ad_submission(
    message: Message,
    state: FSMContext,
    bot: Bot,
    db: Database,
    config: Config,
):
    # Extract text and photo
    photo_id = None
    if message.photo:
        photo_id = message.photo[-1].file_id
        ad_text = message.caption or "Без описания"
    else:
        ad_text = message.text

    if not ad_text or len(ad_text.strip()) < 5:
        await message.answer(
            "⚠️ Анкета слишком короткая. Пожалуйста, заполните анкету по шаблону "
            "и укажите описание товара/услуги.",
            reply_markup=get_cancel_keyboard(),
        )
        return

    user = message.from_user
    username = f"@{user.username}" if user.username else None
    full_name = user.full_name or "Пользователь"

    # Save to database to get unique number
    ad_id = await db.create_ad(
        user_id=user.id,
        username=username,
        full_name=full_name,
        text=ad_text,
        photo_id=photo_id,
    )

    # Publish to channel if configured
    channel_published = False
    bot_info = await bot.get_me()
    channel_kb = get_channel_ad_keyboard(bot_info.username, ad_id)

    channel_text = (
        f"📢 <b>Анкета #{ad_id}</b>\n\n"
        f"{ad_text}\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"ℹ️ <i>Чтобы связаться с продавцом:</i>\n"
        f"Нажмите кнопку ниже или перейдите в бота @{bot_info.username} и выберите «Купить», указав номер <b>#{ad_id}</b>."
    )

    if config.channel_id:
        try:
            if photo_id:
                channel_msg = await bot.send_photo(
                    chat_id=config.channel_id,
                    photo=photo_id,
                    caption=channel_text,
                    parse_mode="HTML",
                    reply_markup=channel_kb,
                )
            else:
                channel_msg = await bot.send_message(
                    chat_id=config.channel_id,
                    text=channel_text,
                    parse_mode="HTML",
                    reply_markup=channel_kb,
                )
            await db.update_channel_message_id(ad_id, channel_msg.message_id)
            channel_published = True
        except Exception as e:
            logger.error(f"Error publishing ad #{ad_id} to channel {config.channel_id}: {e}")

    await state.clear()

    status_extra = ""
    if channel_published:
        status_extra = "📢 <b>Анкета успешно опубликована в канале!</b>\n"
    elif config.channel_id:
        status_extra = "⚠️ <i>Анкета сохранена, но бот не смог отправить её в канал (проверьте, является ли бот администратором канала).</i>\n"

    success_msg = (
        f"✅ <b>Ваша анкета успешно принята!</b>\n\n"
        f"🆔 <b>Присвоен уникальный номер:</b> <code>#{ad_id}</code>\n\n"
        f"{status_extra}"
        f"Когда покупатель введет номер вашей анкеты, бот перешлет её и передаст контакты для связи."
    )

    await message.answer(
        success_msg,
        parse_mode="HTML",
        reply_markup=get_main_keyboard(),
    )


@router.message(SellStates.waiting_for_ad)
async def invalid_ad_format(message: Message):
    await message.answer(
        "⚠️ Пожалуйста, отправьте анкету текстом или фотографией с описанием.",
        reply_markup=get_cancel_keyboard(),
    )
