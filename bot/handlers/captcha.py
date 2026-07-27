import random
import asyncio
import logging
from datetime import datetime
from aiogram import Router, F, Bot
from aiogram.types import Message, ChatMemberUpdated, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ChatPermissions
from aiogram.filters.chat_member_updated import ChatMemberUpdatedFilter, JOIN_TRANSITION

from bot.services.db_service import db_service
from bot.services.redis_service import redis_service

logger = logging.getLogger(__name__)
router = Router(name="captcha_router")

# Datasets
EMOJI_DATASET = [
    ("🍎", "Яблоко"), ("🐶", "Собака"), ("🚗", "Машина"), ("⚽", "Мяч"),
    ("⭐", "Звезда"), ("🍕", "Пицца"), ("🐱", "Кот"), ("🎈", "Шарик"),
    ("🚀", "Ракета"), ("🎁", "Подарок")
]

QUESTIONS_DATASET = [
    ("Сколько дней в одной неделе?", "7", ["5", "7", "10", "12"]),
    ("Какого цвета зеленая трава?", "Зеленый", ["Синий", "Зеленый", "Желтый", "Красный"]),
    ("Сколько лап у кошки?", "4", ["2", "4", "6", "8"]),
    ("Что идет сразу после зимы?", "Весна", ["Осень", "Весна", "Лето", "Ночь"]),
    ("Сколько пальцев на одной руке?", "5", ["3", "5", "8", "10"])
]

CATEGORIES_DATASET = [
    ("Еду (Пища)", [("🍕", "Пицца"), ("🍎", "Яблоко"), ("🍔", "Бургер"), ("🍰", "Торт")], [("🚗", "Авто"), ("🐶", "Пес"), ("🚀", "Ракета"), ("⚽", "Мяч")]),
    ("Животное", [("🐶", "Собака"), ("🐱", "Кот"), ("🦁", "Лев"), ("🐼", "Панда")], [("🍕", "Пицца"), ("🚗", "Авто"), ("🚀", "Ракета"), ("🎈", "Шарик")]),
    ("Транспорт", [("🚗", "Машина"), ("🚀", "Ракета"), ("✈️", "Самолет"), ("🚲", "Велосипед")], [("🍎", "Яблоко"), ("🐶", "Пес"), ("⚽", "Мяч"), ("⭐", "Звезда")])
]

SHAPES_DATASET = [
    ("Синий Квадрат 🟦", "🟦", ["🔴", "🟦", "🔺", "🟡"]),
    ("Красный Круг 🔴", "🔴", ["🔴", "🟩", "⭐", "🔹"]),
    ("Зеленый Квадрат 🟩", "🟩", ["💜", "🟩", "🔺", "🟡"]),
    ("Желтый Круг 🟡", "🟡", ["🟦", "🔴", "🟡", "🔺"])
]

async def start_captcha_background_worker(bot: Bot):
    logger.info("Starting Redis-backed Captcha Expiration Background Worker...")
    while True:
        try:
            await asyncio.sleep(10)
            expired_list = await redis_service.get_expired_captchas()

            for captcha_data in expired_list:
                chat_id = captcha_data.get("chat_id")
                user_id = captcha_data.get("user_id")
                message_id = captcha_data.get("message_id")
                user_fullname = captcha_data.get("user_fullname", "Пользователь")

                if not chat_id or not user_id:
                    continue

                logger.info(f"Captcha expired for user {user_id} in chat {chat_id}. Applying action...")
                await redis_service.delete_captcha(chat_id, user_id)

                settings = await db_service.get_chat_settings(chat_id)
                action = settings.captcha_fail_action.lower() if settings else "kick"

                if message_id:
                    try:
                        await bot.delete_message(chat_id, message_id)
                    except Exception:
                        pass

                if action == "ban":
                    try:
                        await bot.ban_chat_member(chat_id, user_id)
                        await db_service.log_action(
                            chat_id=chat_id,
                            user_id=user_id,
                            user_fullname=user_fullname,
                            action="captcha_failed",
                            reason="Таймаут прохождения капчи (Забанен)"
                        )
                    except Exception as e:
                        logger.error(f"Error banning user on captcha timeout: {e}")
                else:  # Kick
                    try:
                        await bot.ban_chat_member(chat_id, user_id)
                        await bot.unban_chat_member(chat_id, user_id)
                        await db_service.log_action(
                            chat_id=chat_id,
                            user_id=user_id,
                            user_fullname=user_fullname,
                            action="captcha_failed",
                            reason="Таймаут прохождения капчи (Исключен)"
                        )
                    except Exception as e:
                        logger.error(f"Error kicking user on captcha timeout: {e}")

        except Exception as e:
            logger.error(f"Error in captcha background worker: {e}")

@router.chat_member(ChatMemberUpdatedFilter(member_status_changed=JOIN_TRANSITION))
async def on_user_join(event: ChatMemberUpdated, bot: Bot):
    chat_id = event.chat.id
    new_user = event.new_chat_member.user

    if new_user.is_bot:
        return

    # Register user in DB
    await db_service.upsert_user(
        chat_id=chat_id,
        user_id=new_user.id,
        first_name=new_user.first_name,
        last_name=new_user.last_name,
        username=new_user.username,
        is_bot=new_user.is_bot
    )

    settings = await db_service.get_chat_settings(chat_id)
    if not settings or not settings.captcha_enabled:
        return

    # Restrict new member until captcha is solved
    try:
        await bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=new_user.id,
            permissions=ChatPermissions(can_send_messages=False)
        )
    except Exception as e:
        logger.error(f"Error restricting user for captcha: {e}")

    user_fullname = new_user.full_name
    timeout = settings.captcha_timeout
    captcha_type = settings.captcha_type.lower()

    # ROTATION MODE (Random Choice from Allowed Types)
    if captcha_type == "random":
        raw_types = getattr(settings, "captcha_enabled_types", "button,math,math_advanced,emoji,question,category,compare,shapes,sequence")
        allowed_types = [t.strip().lower() for t in raw_types.split(",") if t.strip()]
        if not allowed_types:
            allowed_types = ["button"]
        captcha_type = random.choice(allowed_types)
        logger.info(f"Chat {chat_id}: Rotation picked captcha type '{captcha_type}' for user {new_user.id}")

    # Generate Captcha according to chosen type:
    if captcha_type == "math":
        a, b = random.randint(1, 10), random.randint(1, 10)
        correct_ans = a + b
        options = {correct_ans}
        while len(options) < 4:
            options.add(random.randint(2, 20))
        opts_list = list(options)
        random.shuffle(opts_list)

        buttons = [InlineKeyboardButton(text=str(opt), callback_data=f"captcha:{new_user.id}:{opt}") for opt in opts_list]
        keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
        caption = (
            f"👋 <b>{user_fullname}</b>, добро пожаловать!\n"
            f"Для входа в чат решите пример: <b>{a} + {b} = ?</b>\n"
            f"У вас есть <b>{timeout} секунд</b>."
        )
        answer_key = str(correct_ans)

    elif captcha_type == "math_advanced":
        op = random.choice(["-", "*"])
        if op == "-":
            a = random.randint(10, 30)
            b = random.randint(1, a)
            correct_ans = a - b
        else:
            a = random.randint(2, 6)
            b = random.randint(2, 6)
            correct_ans = a * b

        options = {correct_ans}
        while len(options) < 4:
            options.add(random.randint(0, 36))
        opts_list = list(options)
        random.shuffle(opts_list)

        buttons = [InlineKeyboardButton(text=str(opt), callback_data=f"captcha:{new_user.id}:{opt}") for opt in opts_list]
        keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
        caption = (
            f"👋 <b>{user_fullname}</b>, добро пожаловать!\n"
            f"Для входа в чат решите пример: <b>{a} {op} {b} = ?</b>\n"
            f"У вас есть <b>{timeout} секунд</b>."
        )
        answer_key = str(correct_ans)

    elif captcha_type == "emoji":
        target = random.choice(EMOJI_DATASET)
        correct_emoji, target_name = target
        distractors = [e for e in EMOJI_DATASET if e[0] != correct_emoji]
        chosen_distractors = random.sample(distractors, 3)
        all_options = [target] + chosen_distractors
        random.shuffle(all_options)

        buttons = [InlineKeyboardButton(text=opt[0], callback_data=f"captcha:{new_user.id}:{opt[0]}") for opt in all_options]
        keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
        caption = (
            f"👋 <b>{user_fullname}</b>, добро пожаловать!\n"
            f"Для входа в чат найдите и нажмите на: <b>{target_name} ({correct_emoji})</b>\n"
            f"У вас есть <b>{timeout} секунд</b>."
        )
        answer_key = correct_emoji

    elif captcha_type == "category":
        cat_name, target_items, wrong_items = random.choice(CATEGORIES_DATASET)
        correct_item = random.choice(target_items)
        distractors = random.sample(wrong_items, 3)
        all_opts = [correct_item] + distractors
        random.shuffle(all_opts)

        buttons = [InlineKeyboardButton(text=opt[0], callback_data=f"captcha:{new_user.id}:{opt[0]}") for opt in all_opts]
        keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
        caption = (
            f"👋 <b>{user_fullname}</b>, добро пожаловать!\n"
            f"Для входа в чат выберите из кнопок <b>{cat_name}</b>:\n"
            f"У вас есть <b>{timeout} секунд</b>."
        )
        answer_key = correct_item[0]

    elif captcha_type == "compare":
        num1 = random.randint(10, 50)
        num2 = random.randint(10, 50)
        while num2 == num1:
            num2 = random.randint(10, 50)

        is_bigger = random.choice([True, False])
        if is_bigger:
            correct_num = max(num1, num2)
            word = "БОЛЬШЕ"
        else:
            correct_num = min(num1, num2)
            word = "МЕНЬШЕ"

        buttons = [
            InlineKeyboardButton(text=str(num1), callback_data=f"captcha:{new_user.id}:{num1}"),
            InlineKeyboardButton(text=str(num2), callback_data=f"captcha:{new_user.id}:{num2}")
        ]
        if random.choice([True, False]):
            buttons.reverse()

        keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
        caption = (
            f"👋 <b>{user_fullname}</b>, добро пожаловать!\n"
            f"Какое число <b>{word}</b>? (<b>{num1}</b> или <b>{num2}</b>)\n"
            f"У вас есть <b>{timeout} секунд</b>."
        )
        answer_key = str(correct_num)

    elif captcha_type == "shapes":
        target_name, correct_shape, options_list = random.choice(SHAPES_DATASET)
        opts_copy = list(options_list)
        random.shuffle(opts_copy)

        buttons = [InlineKeyboardButton(text=opt, callback_data=f"captcha:{new_user.id}:{opt}") for opt in opts_copy]
        keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
        caption = (
            f"👋 <b>{user_fullname}</b>, добро пожаловать!\n"
            f"Выберите фигуру: <b>{target_name}</b>\n"
            f"У вас есть <b>{timeout} секунд</b>."
        )
        answer_key = correct_shape

    elif captcha_type == "sequence":
        nums = random.sample(range(1, 99), 4)
        is_min = random.choice([True, False])
        if is_min:
            correct_num = min(nums)
            word = "НАИМЕНЬШЕЕ"
        else:
            correct_num = max(nums)
            word = "НАИБОЛЬШЕЕ"

        buttons = [InlineKeyboardButton(text=str(n), callback_data=f"captcha:{new_user.id}:{n}") for n in nums]
        keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
        caption = (
            f"👋 <b>{user_fullname}</b>, добро пожаловать!\n"
            f"Нажмите на <b>{word}</b> число из списка: <b>{', '.join(map(str, nums))}</b>\n"
            f"У вас есть <b>{timeout} секунд</b>."
        )
        answer_key = str(correct_num)

    elif captcha_type == "question":
        q_text, correct_ans, options_list = random.choice(QUESTIONS_DATASET)
        opts_copy = list(options_list)
        random.shuffle(opts_copy)

        buttons = [InlineKeyboardButton(text=opt, callback_data=f"captcha:{new_user.id}:{opt}") for opt in opts_copy]
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[b] for b in buttons])
        caption = (
            f"👋 <b>{user_fullname}</b>, добро пожаловать!\n"
            f"Ответьте на вопрос: <b>{q_text}</b>\n"
            f"У вас есть <b>{timeout} секунд</b>."
        )
        answer_key = correct_ans

    elif captcha_type == "custom_question" and getattr(settings, "custom_captcha_question", None) and getattr(settings, "custom_captcha_answer", None):
        q_text = settings.custom_captcha_question
        correct_ans = settings.custom_captcha_answer.strip()
        
        # Generate 3 dummy distractor options
        distractors = ["Правило 1", "Правило 2", "Отмена"]
        opts = [correct_ans] + distractors
        random.shuffle(opts)

        buttons = [InlineKeyboardButton(text=opt, callback_data=f"captcha:{new_user.id}:{opt}") for opt in opts]
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[b] for b in buttons])
        caption = (
            f"👋 <b>{user_fullname}</b>, добро пожаловать!\n"
            f"Вопрос сообщества: <b>{q_text}</b>\n"
            f"У вас есть <b>{timeout} секунд</b>."
        )
        answer_key = correct_ans

    else:
        # Default Button Captcha
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🟢 Я не робот (Нажмите)", callback_data=f"captcha:{new_user.id}:ok")
        ]])
        caption = (
            f"👋 <b>{user_fullname}</b>, добро пожаловать!\n"
            f"Подтвердите, что вы не робот, нажав кнопку ниже.\n"
            f"У вас есть <b>{timeout} секунд</b>."
        )
        answer_key = "ok"

    captcha_msg = await bot.send_message(chat_id, caption, reply_markup=keyboard)

    await redis_service.set_captcha(
        chat_id=chat_id,
        user_id=new_user.id,
        answer=answer_key,
        message_id=captcha_msg.message_id,
        user_fullname=user_fullname,
        timeout=timeout
    )

@router.callback_query(F.data.startswith("captcha:"))
async def on_captcha_callback(callback: CallbackQuery, bot: Bot):
    parts = callback.data.split(":")
    if len(parts) != 3:
        return

    target_user_id = int(parts[1])
    user_answer = parts[2]
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    if user_id != target_user_id:
        await callback.answer("❌ Эта капча предназначена для другого пользователя!", show_alert=True)
        return

    captcha_data = await redis_service.get_captcha(chat_id, user_id)
    if not captcha_data:
        await callback.answer("⚠️ Капча устарела или уже была пройдена.", show_alert=True)
        return

    correct_answer = captcha_data.get("answer")

    if user_answer.strip().lower() == correct_answer.strip().lower():
        await redis_service.delete_captcha(chat_id, user_id)
        await callback.answer("✅ Капча успешно пройдена! Добро пожаловать.")

        # Unmute user
        try:
            await bot.restrict_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                permissions=ChatPermissions(
                    can_send_messages=True,
                    can_send_audios=True,
                    can_send_documents=True,
                    can_send_photos=True,
                    can_send_videos=True,
                    can_send_video_notes=True,
                    can_send_voice_notes=True,
                    can_send_polls=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True,
                    can_invite_users=True
                )
            )
        except Exception:
            pass

        # Delete captcha message
        try:
            await callback.message.delete()
        except Exception:
            pass

        user_fullname = callback.from_user.full_name
        await db_service.log_action(
            chat_id=chat_id,
            user_id=user_id,
            user_fullname=user_fullname,
            action="captcha_passed",
            reason="Капча успешно пройдена"
        )

        settings = await db_service.get_chat_settings(chat_id)
        if settings and settings.welcome_message_enabled and settings.welcome_text:
            welcome_msg = await bot.send_message(
                chat_id,
                f"🎉 <b>{user_fullname}</b>, {settings.welcome_text}"
            )
            if settings.bot_auto_delete_seconds > 0:
                async def delete_later(m, delay):
                    await asyncio.sleep(delay)
                    try:
                        await m.delete()
                    except Exception:
                        pass
                asyncio.create_task(delete_later(welcome_msg, settings.bot_auto_delete_seconds))
    else:
        await callback.answer("❌ Неверный ответ! Попробуйте еще раз.", show_alert=True)
