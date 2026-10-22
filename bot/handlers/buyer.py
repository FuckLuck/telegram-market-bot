import logging
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from bot.database import Database
from bot.states import BuyStates
from bot.keyboards import (
    get_main_keyboard,
    get_cancel_keyboard,
    get_seller_contact_keyboard,
)

logger = logging.getLogger(__name__)
router = Router()


@router.message(F.text == "🛒 Купить")
@router.message(Command("buy"))
async def start_buy(message: Message, state: FSMContext):
    await state.set_state(BuyStates.waiting_for_ad_number)
    await message.answer(
        "🔢 <b>Поиск анкеты для покупки</b>\n\n"
        "Отправьте номер анкеты из канала (например: <code>1001</code> или <code>#1001</code>):",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard(),
    )


@router.message(BuyStates.waiting_for_ad_number, F.text)
async def process_ad_number(
    message: Message,
    state: FSMContext,
    bot: Bot,
    db: Database,
):
    raw_text = message.text.strip().lstrip("#").lstrip("№").strip()

    if not raw_text.isdigit():
        await message.answer(
            "⚠️ Пожалуйста, введите корректный числовой номер анкеты (например, <code>1001</code>).\n"
            "Или нажмите «❌ Отмена», чтобы выйти в меню.",
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard(),
        )
        return

    ad_id = int(raw_text)
    ad = await db.get_ad(ad_id)

    if not ad:
        await message.answer(
            f"❌ <b>Анкета #{ad_id} не найдена.</b>\n\n"
            "Пожалуйста, проверьте правильность введенного номера или нажмите «❌ Отмена».",
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard(),
        )
        return

    seller_username = ad.get("username")
    seller_id = ad.get("user_id")
    seller_name = ad.get("full_name") or "Продавец"

    if seller_username:
        clean_user = seller_username.lstrip("@")
        seller_contact_display = f"@{clean_user}"
    else:
        seller_contact_display = (
            f'<a href="tg://user?id={seller_id}">{seller_name}</a> (юзернейм не установлен)'
        )

    response_text = (
        f"📋 <b>Анкета #{ad['id']}</b>\n\n"
        f"{ad['text']}\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Продавец:</b> {seller_contact_display}"
    )

    contact_kb = get_seller_contact_keyboard(seller_username, seller_id)

    if ad.get("photo_id"):
        await message.answer_photo(
            photo=ad["photo_id"],
            caption=response_text,
            parse_mode="HTML",
            reply_markup=contact_kb,
        )
    else:
        await message.answer(
            text=response_text,
            parse_mode="HTML",
            reply_markup=contact_kb,
        )

    # Optionally notify the seller that someone looked up their ad
    if seller_id != message.from_user.id:
        try:
            buyer_display = (
                f"@{message.from_user.username}"
                if message.from_user.username
                else message.from_user.full_name
            )
            await bot.send_message(
                chat_id=seller_id,
                text=(
                    f"🔔 Пользователь <b>{buyer_display}</b> запросил контакты "
                    f"по вашей анкете <b>#{ad_id}</b>!"
                ),
                parse_mode="HTML",
            )
        except Exception as e:
            logger.debug(f"Could not notify seller about ad #{ad_id}: {e}")

    await state.clear()
    await message.answer(
        "Вы можете продолжить поиск или выбрать действие в меню:",
        reply_markup=get_main_keyboard(),
    )


@router.message(BuyStates.waiting_for_ad_number)
async def invalid_number_input(message: Message):
    await message.answer(
        "⚠️ Пожалуйста, отправьте текстовый номер анкеты (например, <code>1001</code>).",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard(),
    )
