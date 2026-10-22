from aiogram import Router, F
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from bot.database import Database
from bot.keyboards import (
    get_main_keyboard,
    get_seller_contact_keyboard,
)

router = Router()


@router.message(CommandStart())
async def handle_start(
    message: Message,
    command: CommandObject,
    state: FSMContext,
    db: Database,
):
    await state.clear()

    # Handle deep-linking from channel (e.g. /start ad_1001)
    if command.args and command.args.startswith("ad_"):
        raw_id = command.args.replace("ad_", "").strip()
        if raw_id.isdigit():
            ad_id = int(raw_id)
            ad = await db.get_ad(ad_id)
            if ad:
                seller_username = ad.get("username")
                seller_id = ad.get("user_id")
                seller_name = ad.get("full_name") or "Продавец"

                if seller_username:
                    clean_user = seller_username.lstrip("@")
                    seller_contact = f"@{clean_user}"
                else:
                    seller_contact = (
                        f'<a href="tg://user?id={seller_id}">{seller_name}</a>'
                    )

                text = (
                    f"📋 <b>Анкета #{ad['id']}</b>\n\n"
                    f"{ad['text']}\n\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"👤 <b>Продавец:</b> {seller_contact}"
                )

                contact_kb = get_seller_contact_keyboard(
                    seller_username, seller_id
                )

                if ad.get("photo_id"):
                    await message.answer_photo(
                        photo=ad["photo_id"],
                        caption=text,
                        parse_mode="HTML",
                        reply_markup=contact_kb,
                    )
                else:
                    await message.answer(
                        text=text,
                        parse_mode="HTML",
                        reply_markup=contact_kb,
                    )

                await message.answer(
                    "Вы можете продолжить работу, выбрав действие в меню:",
                    reply_markup=get_main_keyboard(),
                )
                return

    welcome_text = (
        f"👋 Здравствуйте, <b>{message.from_user.first_name}</b>!\n\n"
        "Добро пожаловать на торговую площадку.\n\n"
        "<b>Возможности бота:</b>\n"
        "📢 <b>Продать</b> — заполнить анкету и опубликовать объявление в канале.\n"
        "🛒 <b>Купить</b> — найти анкету по номеру и получить контакты продавца.\n\n"
        "Выберите действие с помощью кнопок ниже:"
    )
    await message.answer(
        welcome_text,
        parse_mode="HTML",
        reply_markup=get_main_keyboard(),
    )


@router.message(F.text == "❌ Отмена")
@router.message(Command("cancel"))
async def handle_cancel(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()
        await message.answer(
            "Действие отменено. Вы вернулись в главное меню.",
            reply_markup=get_main_keyboard(),
        )
    else:
        await message.answer(
            "Вы в главном меню.",
            reply_markup=get_main_keyboard(),
        )


@router.message(F.text == "ℹ️ Помощь")
@router.message(Command("help"))
async def handle_help(message: Message):
    help_text = (
        "📖 <b>Инструкция по использованию бота:</b>\n\n"
        "🔹 <b>Как разместить объявление (Продать):</b>\n"
        "1. Нажмите кнопку «📢 Продать».\n"
        "2. Скопируйте шаблон анкеты, заполните его и отправьте боту (можно с фото).\n"
        "3. Бот присвоит анкете уникальный номер (например, #1001) и опубликует её в канале.\n\n"
        "🔹 <b>Как связаться с продавцом (Купить):</b>\n"
        "1. Найдите понравившееся объявление в канале и запомните его номер.\n"
        "2. Нажмите кнопку «🛒 Купить» в боте (или кнопку под постом в канале).\n"
        "3. Отправьте номер анкеты боту.\n"
        "4. Бот пришлет анкету и юзернейм продавца для связи.\n\n"
        "🔹 <b>Команды:</b>\n"
        "/start — Перезапуск бота / Главное меню\n"
        "/cancel — Отмена текущего действия\n"
        "/my_ads — Просмотр ваших размещенных анкет\n"
        "/help — Эта справка"
    )
    await message.answer(
        help_text,
        parse_mode="HTML",
        reply_markup=get_main_keyboard(),
    )


@router.message(F.text == "📋 Мои анкеты")
@router.message(Command("my_ads"))
async def handle_my_ads(message: Message, db: Database):
    user_ads = await db.get_user_ads(message.from_user.id)
    if not user_ads:
        await message.answer(
            "У вас пока нет размещенных анкет.\n"
            "Нажмите «📢 Продать», чтобы создать первое объявление!",
            reply_markup=get_main_keyboard(),
        )
        return

    text_lines = ["📋 <b>Ваши размещенные анкеты:</b>\n"]
    for ad in user_ads:
        preview = ad["text"].split("\n")[0][:40]
        text_lines.append(f"• <b>#{ad['id']}</b> — {preview}...")

    text_lines.append(
        "\n<i>Покупатели могут найти ваши объявления по этим номерам.</i>"
    )

    await message.answer(
        "\n".join(text_lines),
        parse_mode="HTML",
        reply_markup=get_main_keyboard(),
    )
