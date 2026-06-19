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

# ====================== НАСТРОЙКИ ======================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

load_dotenv()

# Проверка токена
if not os.getenv("TELEGRAM_TOKEN"):
    logging.error("❌ TELEGRAM_TOKEN не задан в .env файле!")
    exit(1)

bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
dp = Dispatcher()
assistant = BirthdayAssistant()
scheduler = AsyncIOScheduler()

# ====================== ОБРАБОТЧИКИ ======================

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "🎉 <b>Birthday Guardian</b> — работает\n\n"
        "Команды:\n"
        "/list — все дни рождения\n"
        "/nearest — ближайшие 30 дней\n"
        "/today — сегодня\n"
        "/delete ID — удалить запись",
        parse_mode="HTML"
    )

@dp.message(Command("list"))
async def cmd_list(message: types.Message):
    try:
        session = Session()
        birthdays = session.query(Birthday).order_by(Birthday.birth_date).all()
        
        if not birthdays:
            return await message.answer("📭 Пока нет дней рождения.")
        
        text = f"📋 <b>Все дни рождения ({len(birthdays)}):</b>\n\n"
        current_month = None
        for b in birthdays:
            month = b.birth_date.month
            if month != current_month:
                text += f"\n📅 <b>{b.birth_date.strftime('%B')}</b>\n"
                current_month = month
            text += f"🎂 {b.name} — {b.birth_date.strftime('%d.%m')}\n"
        await message.answer(text, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Ошибка в /list: {e}")
        await message.answer("❌ Ошибка при получении списка.")

@dp.message(Command("nearest"))
async def cmd_nearest(message: types.Message):
    try:
        session = Session()
        today = datetime.date.today()
        end_date = today + datetime.timedelta(days=30)
        
        birthdays = session.query(Birthday).filter(
            Birthday.birth_date >= today,
            Birthday.birth_date <= end_date
        ).order_by(Birthday.birth_date).all()
        
        if not birthdays:
            return await message.answer("🎉 В ближайшие 30 дней нет дней рождения.")
        
        text = "🔥 <b>Ближайшие дни рождения:</b>\n\n"
        for b in birthdays:
            days_left = (b.birth_date - today).days
            text += f"🎂 {b.name} — {b.birth_date.strftime('%d.%m')} (через {days_left} дней)\n"
        await message.answer(text, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Ошибка в /nearest: {e}")
        await message.answer("❌ Ошибка при получении ближайших ДР.")

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
        await message.answer("Использование: /delete ID\nСначала выполни /list")

async def check_birthdays_today(message=None):
    try:
        session = Session()
        today = datetime.date.today()
        birthdays = session.query(Birthday).filter(
            Birthday.birth_date.like(f"%-{today.month:02d}-{today.day:02d}")
        ).all()
        
        if not birthdays and message:
            return await message.answer("🎉 Сегодня никто не празднует.")
        
        for b in birthdays:
            age = today.year - b.birth_date.year
            cong = await assistant.generate_congratulation(b.name, age)
            text = f"🎂 <b>Сегодня день рождения у {b.name}!</b>\n\n{cong}"
            if message:
                await message.answer(text, parse_mode="HTML")
            else:
                await bot.send_message(chat_id=33936200, text=text, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Ошибка в check_birthdays_today: {e}")

async def main():
    try:
        init_db()
        print("🎉 Birthday Guardian запущен!")
        scheduler.add_job(check_birthdays_today, 'cron', hour=9, minute=0)
        scheduler.start()
        logging.info("Планировщик напоминаний активирован")
        await dp.start_polling(bot)
    except Exception as e:
        logging.critical(f"Критическая ошибка запуска: {e}")

if __name__ == "__main__":
    asyncio.run(main())