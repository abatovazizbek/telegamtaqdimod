import os
import asyncio
import google.generativeai as genai
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command

# 1. Railway Variables - SKRINSHOTDAGI NOM BILAN BIR XIL QILINDI
# Railway'da nima deb yozgan bo'lsangiz, shu yerga o'shani yozish shart!
TOKEN_VAL = os.environ.get("8128500951:AAFsgE6uq8eX2kY8_yxFnCLajzrEE3p7EtY")
GEMINI_VAL = os.environ.get("AIzaSyDMFlvMD-VMDkOeNitUzBjSzNy1a3L2Xj0")

# Gemini AI-ni sozlash
if GEMINI_VAL:
    genai.configure(api_key=GEMINI_VAL)
    model = genai.GenerativeModel('gemini-1.5-flash')

# Botni yoqish
bot = Bot(token=TOKEN_VAL)
dp = Dispatcher()

# /start komandasi
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Salom! Bot ishga tushdi. ✅\n\nMavzu yozing, taqdimot matnini tayyorlayman.")

# Xabarlarni qabul qilish
@dp.message(F.text)
async def handle_message(message: types.Message):
    if not GEMINI_VAL:
        await message.answer("Xato: GEMINI_KEY topilmadi.")
        return

    try:
        response = model.generate_content(message.text)
        await message.answer(response.text)
    except Exception as e:
        await message.answer(f"Xatolik: {str(e)[:50]}")

async def main():
    # Bot pollingni boshlaydi
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
