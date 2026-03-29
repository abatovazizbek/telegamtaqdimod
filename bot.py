import asyncio
import google.generativeai as genai
from aiogram import Bot, Dispatcher, F, types

# --- 1. MA'LUMOTLARNI TO'G'RIDAN-TO'G'RI YOZISH ---
# Railway-dagi o'zgaruvchilar endi shart emas
TOKEN = "8128500951:AAFsgE6uq8eX2kY8_yxFnCLajzrEE3p7EtY"
API_KEY = "AIzaSyDMFlvMD-VMDkOeNitUzBjSzNy1a3L2Xj0"

# --- 2. SOZLAMALAR ---
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- 3. BOT FUNKSIYALARI ---
@dp.message(F.text == "/start")
async def welcome(message: types.Message):
    await message.answer("Bot to'g'ridan-to'g'ri ulanish orqali ishga tushdi! ✅")

@dp.message(F.text)
async def ai_answer(message: types.Message):
    try:
        response = model.generate_content(message.text)
        await message.answer(response.text)
    except Exception as e:
        await message.answer(f"Xatolik yuz berdi: {str(e)[:50]}")

async def main():
    print("Bot pollingni boshladi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
