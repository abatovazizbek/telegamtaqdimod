import os
import asyncio
import logging
import io
import traceback
import google.generativeai as genai
from aiogram import Bot, Dispatcher, F, types

# 1. SOZLAMALAR
TOKEN = "8128500951:AAFsgE6uq8eX2kY8_yxFnCLajzrEE3p7EtY"
GEMINI_API_KEY = os.getenv("AIzaSyBzg_66XVCdCX2JYRObFNVOZYAkpHcNptM")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# 2. GEMINI TEST
try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    logging.info("Gemini tayyor!")
except Exception as e:
    logging.error(f"Gemini ulanishda xato: {e}")

@dp.message(F.text)
async def debug_handler(message: types.Message):
    await message.answer("🔍 Tekshirilmoqda...")
    
    try:
        # TEST 1: Gemini bilan aloqa
        await message.answer("1. Gemini modeliga so'rov yuborilyapti...")
        response = model.generate_content("Salom, qisqa javob ber.")
        await message.answer(f"✅ Gemini javob berdi: {response.text[:50]}")
        
        # TEST 2: Kutubxonalar (pptx)
        await message.answer("2. 'python-pptx' kutubxonasi tekshirilyapti...")
        from pptx import Presentation
        prs = Presentation()
        await message.answer("✅ 'python-pptx' muvaffaqiyatli yuklandi.")
        
    except Exception as e:
        # XATONI TO'LIQ KO'RSATISH
        error_trace = traceback.format_exc()
        await message.answer(f"❌ ANIQLANGAN XATO:\n\n<code>{error_trace[:3000]}</code>", parse_mode="HTML")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
