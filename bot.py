import os
import asyncio
from aiogram import Bot, Dispatcher, F, types
import google.generativeai as genai

# Railway-da yozilgan nomlarni avtomatik qidirish
# Siz kod ichiga hech narsa yozishingiz shart emas!
TOKEN = os.environ.get("8128500951:AAFsgE6uq8eX2kY8_yxFnCLajzrEE3p7EtY") or os.environ.get("8128500951:AAFsgE6uq8eX2kY8_yxFnCLajzrEE3p7EtY")
API_KEY = os.environ.get("AIzaSyDMFlvMD-VMDkOeNitUzBjSzNy1a3L2Xj0") or os.environ.get("AIzaSyDMFlvMD-VMDkOeNitUzBjSzNy1a3L2Xj0")

# Bot va AI-ni sozlash
bot = Bot(token=TOKEN) if TOKEN else None
dp = Dispatcher()

if API_KEY:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')

@dp.message(F.text == "/start")
async def start(message: types.Message):
    await message.answer("Salom! Bot tayyor. Mavzu yozing.")

@dp.message(F.text)
async def chat(message: types.Message):
    try:
        # AI-dan javob olish
        response = model.generate_content(message.text)
        await message.answer(response.text)
    except Exception:
        await message.answer("Tizimda ulanish xatosi (API kalitni tekshiring).")

async def main():
    if bot:
        await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
