import os
import json
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
import aiosqlite
from datetime import datetime
import subprocess

API_TOKEN = ""
ADMIN_ID =   # Id админа для уведомлений

logging.basicConfig(level=logging.INFO)
bot = Bot(API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class Form(StatesGroup):
    waiting_term = State()
    waiting_payment_confirm = State()
    waiting_steamid = State()
    selected_category = State()
    selected_term = State()
    waiting_payment_screenshot = State()  # новое состояние для скриншота

PRIVILEGES = {
    "VIP": {"7 днів": 50, "1 місяць": 100, "Назавжди": 200},
    "Osiris": {"7 днів": 150, "1 місяць": 300, "Назавжди": 400},
    "Zeus": {"7 днів": 500, "1 місяць": 1000, "Назавжди": 1200},
    "Odin": {"7 днів": 450, "1 місяць": 700, "Назавжди": 1400},
    "Thor": {"7 днів": 550, "1 місяць": 1100, "Назавжди": 2200},
    "Anubis": {"7 днів": 1200, "1 місяць": 2200, "Назавжди": 4400},
    "Создатель": {"Назавжди": 6000}
}

async def init_db():
    async with aiosqlite.connect("orders.db") as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_user_id INTEGER,
            tg_username TEXT,
            privilege TEXT,
            term TEXT,
            amount INTEGER,
            status TEXT,
            created_at TEXT,
            paid_at TEXT,
            steam_id TEXT
        );
        """)
        await db.commit()

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    kb = types.InlineKeyboardMarkup(row_width=2)
    for priv in PRIVILEGES.keys():
        kb.insert(types.InlineKeyboardButton(priv, callback_data=f"select_category:{priv}"))
    await message.answer("🔹 Вітаю! Обери привілею:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("select_category:"))
async def select_category(callback: types.CallbackQuery, state: FSMContext):
    category = callback.data.split(":")[1]
    kb = types.InlineKeyboardMarkup(row_width=1)
    terms = PRIVILEGES[category].keys()
    for term in terms:
        price = PRIVILEGES[category][term]
        kb.add(types.InlineKeyboardButton(f"{term} — {price} UAH", callback_data=f"select_term:{category}|{term}"))
    await callback.message.answer(f"🔸 Обери термін дії привілеї <b>{category}</b>:", parse_mode="HTML", reply_markup=kb)
    await state.update_data(selected_category=category)

@dp.callback_query_handler(lambda c: c.data.startswith("select_term:"))
async def select_term(callback: types.CallbackQuery, state: FSMContext):
    category, term = callback.data.split(":")[1].split("|")
    price = PRIVILEGES[category][term]
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("💳 Monobank", callback_data="pay_mono"),
        types.InlineKeyboardButton("💳 PrivatBank", callback_data="pay_privat")
    )
    await callback.message.answer(
        f"💰 Ти обрав: <b>{category}</b> на <b>{term}</b> Сума: <b>{price} UAH</b>\n\nОбери спосіб оплати:",
        parse_mode="HTML", reply_markup=kb
    )
    await state.update_data(selected_term=term, selected_price=price)
    await Form.waiting_payment_confirm.set()

@dp.callback_query_handler(lambda c: c.data == "pay_mono", state=Form.waiting_payment_confirm)
async def pay_mono(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await callback.message.answer(
        f"💳 Оплата через Monobank\n\nПривілея: <b>{data['selected_category']}</b>\nТермін: <b>{data['selected_term']}</b>\nСума: <b>{data['selected_price']} UAH</b>\n➡️ Номер карти: <code>4441 1110 1806 7706</code>\nПісля оплати надішли сюди скріншот.",
        parse_mode="HTML"
    )
    await Form.waiting_payment_screenshot.set()  # Перехід в стан очікування скриншота

@dp.callback_query_handler(lambda c: c.data == "pay_privat", state=Form.waiting_payment_confirm)
async def pay_privat(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await callback.message.answer(
        f"💳 Оплата через PrivatBank\n\nПривілея: <b>{data['selected_category']}</b>\nТермін: <b>{data['selected_term']}</b>\nСума: <b>{data['selected_price']} UAH</b>\n➡️ Номер карти: <code>5168 7451 9690 9789</code>\nПісля оплати надішли сюди скріншот.",
        parse_mode="HTML"
    )
    await Form.waiting_payment_screenshot.set()  # Перехід в стан ожидания скриншота

@dp.message_handler(content_types=types.ContentType.PHOTO, state=Form.waiting_payment_screenshot)
async def handle_screenshot(message: types.Message, state: FSMContext):
    # Получаем фото
    file_id = message.photo[-1].file_id
    file = await bot.get_file(file_id)
    file_path = file.file_path

    # Скачиваем фото
    photo = await bot.download_file(file_path)
    photo_path = f"payment_screenshots/{file_id}.jpg"
    
    os.makedirs(os.path.dirname(photo_path), exist_ok=True)
    with open(photo_path, "wb") as f:
        f.write(photo)

    # Сохраняем информацию в базу данных или отправляем админу для проверки
    data = await state.get_data()

    # Отправляем скриншот админу
    await bot.send_photo(ADMIN_ID, photo, caption="Платіжний скріншот на перевірку")

    # Отправляем уведомление пользователю
    await message.answer(f"✅ Скріншот оплати отримано! Чекайте на підтвердження.")
    
    # Уведомление админу
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("✅ Схвалено", callback_data="approve_payment"),
        types.InlineKeyboardButton("❌ Відхилено", callback_data="reject_payment")
    )
    await bot.send_message(ADMIN_ID, "Нове замовлення на перевірку!", reply_markup=kb)
    
    await state.finish()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(init_db())
    executor.start_polling(dp, skip_updates=True)

