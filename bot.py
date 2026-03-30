import asyncio
import google.generativeai as genai
from aiogram import Bot, Dispatcher, F, types

# 1. MA'LUMOTLAR (Sizning tokeningiz joylashtirildi)
TOKEN = "8128500951:AAFsgE6uq8eX2kY8_yxFnCLajzrEE3p7EtY"
GEMINI_API_KEY = "AIzaSyDMFlvMD-VMDkOeNitUzBjSzNy1a3L2Xj0"

# 2. SOZLAMALAR
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

bot = Bot(token=TOKEN)
dp = Dispatcher()

# 3. BOT BUYRUQLARI
@dp.message(F.text == "/start")
async def welcome(message: types.Message):
    await message.answer("Bot muvaffaqiyatli ishga tushdi! ✅\nEndi savol berishingiz mumkin.")

@dp.message(F.text)
async def ai_answer(message: types.Message):
    try:
        response = model.generate_content(message.text)
        await message.answer(response.text)
    except Exception as e:
        await message.answer(f"Xato yuz berdi: {str(e)[:50]}")

# 4. ASOSIY QISM (Conflict'ni yo'qotadigan qism)
async def main():
    # MANA SHU QATOR BRAUZERDAGI HAVOLA BILAN BIR XIL ISHNI QILADI:
    print("Eski ulanishlar tozalanmoqda...")
    await bot.delete_webhook(drop_pending_updates=True)
    
    print("Bot pollingni boshladi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
