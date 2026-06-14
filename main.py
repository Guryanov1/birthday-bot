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
        "🎉 <b>Birthday Guardian</b> — активен\n\n"
        "Основные команды:\n"
        "/list — все дни рождения\n"
        "/nearest — ближайшие 30 дней\n"
        "/today — сегодня\n"
        "/delete ID — удалить запись",
        parse_mode="HTML"
    )

@dp.message(Command("list"))
async def cmd_list(message: types.Message):
    session = Session()
    birthdays = session.query(Birthday).order_by(Birthday.birth_date).all()
    
    if not birthdays:
        return await message.answer("📭 Нет записей.")
    
    text = f"📋 <b>Все дни рождения ({len(birthdays)}):</b>\n\n"
    for b in birthdays[:50]:
        text += f"🎂 {b.name} — {b.birth_date.strftime('%d.%m')}\n"
    if len(birthdays) > 50:
        text += f"\n... и ещё {len(birthdays)-50} человек"
    await message.answer(text)

@dp.message(Command("nearest"))
async def cmd_nearest(message: types.Message):
    session = Session()
    today = datetime.date.today()
    end_date = today + datetime.timedelta(days=30)
    
    birthdays = session.query(Birthday).filter(
        Birthday.birth_date.between(today, end_date)
    ).order_by(Birthday.birth_date).all()
    
    if not birthdays:
        return await message.answer("🎉 В ближайшие 30 дней нет дней рождения.")
    
    text = "🔥 <b>Ближайшие дни рождения:</b>\n\n"
    for b in birthdays:
        days_left = (b.birth_date - today).days
        text += f"🎂 {b.name} — {b.birth_date.strftime('%d.%m')} (через {days_left} дней)\n"
    await message.answer(text, parse_mode="HTML")

@dp.message(Command("today"))
async def cmd_today(message: types.Message):
    await check_birthdays_today(message)

@dp.message(Command("delete"))
async def cmd_delete(message: types.Message):
    try:
        record_id = int(message.text.split()[1])
        session = Session()
        record = session.query(Birthday).get(record_id)
        if record:
            name = record.name
            session.delete(record)
            session.commit()
            await message.answer(f"✅ Удалено: {name}")
        else:
            await message.answer("❌ Запись не найдена.")
    except:
        await message.answer("Использование: /delete ID\n\nID можно увидеть в команде /list")

async def check_birthdays_today(message=None):
    try:
        session = Session()
        today = datetime.date.today()
        birthdays = session.query(Birthday).filter(
            Birthday.birth_date.like(f"%-{today.month:02d}-{today.day:02d}")
        ).all()
        
        if not birthdays:
            if message:
                await message.answer("🎉 Сегодня никто не празднует.")
            return
        
        for b in birthdays:
            age = today.year - b.birth_date.year
            cong = await assistant.generate_congratulation(b.name, age)
            text = f"🎂 <b>Сегодня день рождения у {b.name}!</b>\n\n{cong}"
            if message:
                await message.answer(text, parse_mode="HTML")
            else:
                await bot.send_message(chat_id=33936200, text=text, parse_mode="HTML")
    except Exception as e:
        print(f"Ошибка: {e}")

async def main():
    init_db()
    print("🎉 Birthday Guardian запущен!")
    scheduler.add_job(check_birthdays_today, 'cron', hour=9, minute=0)
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())