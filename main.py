import asyncio
import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram import types
from database import init_db, Session, Birthday
from agent import BirthdayAssistant
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import datetime

logging.basicConfig(level=logging.INFO)

load_dotenv()

bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
dp = Dispatcher()
assistant = BirthdayAssistant()
scheduler = AsyncIOScheduler()

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "🎉 <b>Birthday Guardian</b>\n\n"
        "Команды:\n"
        "/list — все дни рождения\n"
        "/nearest — ближайшие 30 дней\n"
        "/today — сегодня",
        parse_mode="HTML"
    )

@dp.message(Command("list"))
async def cmd_list(message: types.Message):
    session = Session()
    birthdays = session.query(Birthday).order_by(Birthday.birth_date).all()
    if not birthdays:
        return await message.answer("📭 Нет записей.")
    text = f"📋 Всего: {len(birthdays)}\n\n"
    for b in birthdays[:50]:
        text += f"🎂 {b.name} — {b.birth_date.strftime('%d.%m')}\n"
    await message.answer(text)

@dp.message(Command("nearest"))
async def cmd_nearest(message: types.Message):
    session = Session()
    today = datetime.date.today()
    upcoming = []
    
    for b in session.query(Birthday).all():
        try:
            this_year = datetime.date(today.year, b.birth_date.month, b.birth_date.day)
            if this_year < today:
                this_year = datetime.date(today.year + 1, b.birth_date.month, b.birth_date.day)
            
            days_left = (this_year - today).days
            if 0 <= days_left <= 30:
                upcoming.append((b, days_left))
        except:
            continue
    
    if not upcoming:
        return await message.answer("🎉 В ближайшие 30 дней нет дней рождения.")
    
    upcoming.sort(key=lambda x: x[1])
    
    text = "🔥 <b>Ближайшие дни рождения:</b>\n\n"
    for b, days in upcoming:
        text += f"🎂 {b.name} — {b.birth_date.strftime('%d.%m')} (через {days} дней)\n"
    
    await message.answer(text, parse_mode="HTML")

@dp.message(Command("today"))
async def cmd_today(message: types.Message):
    await message.answer("Проверка сегодня...")

async def main():
    init_db()
    print("🎉 Birthday Guardian запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())