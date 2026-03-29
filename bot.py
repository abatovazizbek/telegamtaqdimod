import os
import asyncio
import google.generativeai as genai
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command

# --- 1. RAILWAY VARIABLES (Maksimal ishonchli qidiruv) ---
# Skrinshotingizdagi nomlar bilan bir xil qilindi
TOKEN = os.environ.get("8128500951:AAFsgE6uq8eX2kY8_yxFnCLajzrEE3p7EtY")
GEMINI_KEY = os.environ.get("AIzaSyDMFlvMD-VMDkOeNitUzBjSzNy1a3L2Xj0")

# --- 2. LOGLARDA TEKSHIRISH (Railway Deploy Logs-da ko'rinadi) ---
print("--- TIZIM TEKSHIRUVI ---")
if TOKEN:
    print(f"✅ TOKEN topildi: {TOKEN[:5]}***")
else:
    print("❌ XATO: TOKEN o'zgaruvchisi Railway-da topilmadi!")

if GEMINI_KEY:
    print(f"✅ GEMINI_KEY topildi: {GEMINI_KEY[:5]}***")
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    print("❌ XATO: GEMINI_KEY o'zgaruvchisi Railway-da topilmadi!")

# --- 3. BOTNI YOQISH ---
if not TOKEN:
    # Token bo'lmasa botni yoqishga urinmaymiz
    raise ValueError("Dastur to'xtatildi: Token mavjud emas.")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# /start buyrug'i
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Salom! Bot muvaffaqiyatli ishlamoqda. ✅\n\nMavzu yuboring, Gemini javob beradi.")

# AI bilan muloqot
@dp.message(F.text)
async def handle_ai(message: types.Message):
    if not GEMINI_KEY:
        await message.answer("Tizimda API kalit topilmadi.")
        return

    try:
        response = model.generate_content(message.text)
        await message.answer(response.text)
    except Exception as e:
        await message.answer(f"Xatolik yuz berdi: {str(e)[:100]}")

async def main():
    print("--- BOT POLLING BOSHLANDI ---")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot to'xtatildi.")
