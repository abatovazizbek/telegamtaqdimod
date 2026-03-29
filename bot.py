import asyncio
import google.generativeai as genai
from aiogram import Bot, Dispatcher, F, types

# Ma'lumotlaringiz
TOKEN = "8128500951:AAFsgE6uq8eX2kY8_yxFnCLajzrEE3p7EtY"
API_KEY = "AIzaSyDMFlvMD-VMDkOeNitUzBjSzNy1a3L2Xj0"

# Gemini sozlash
genai.configure(api_key=API_KEY)

# MODEL NOMINI TO'G'RI YOZISH
# Agar gemini-1.5-flash ishlamasa, 'gemini-pro' deb yozib ko'ring
model = genai.GenerativeModel('gemini-1.5-flash')

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(F.text == "/start")
async def welcome(message: types.Message):
    await message.answer("Bot ulandi! Savolingizni bering.")

@dp.message(F.text)
async def ai_answer(message: types.Message):
    try:
        # AI javobini olish
        response = model.generate_content(message.text)
        await message.answer(response.text)
    except Exception as e:
        # Xatolikni to'liq ko'rish uchun logga chiqaramiz
        print(f"Xato: {e}")
        await message.answer("Kechirasiz, hozir javob bera olmayman. Model ulanishida xatolik.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
