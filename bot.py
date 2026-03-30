import asyncio
import logging
import re
import google.generativeai as genai
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from pptx import Presentation
import io

# 1. MA'LUMOTLAR (Nusxalash esdan chiqmasin)
TOKEN = "8128500951:AAFsgE6uq8eX2kY8_yxFnCLajzrEE3p7EtY"
GEMINI_API_KEY = "AIzaSyDMFlvMD-VMDkOeNitUzBjSzNy1a3L2Xj0"

# Logging sozlash
logging.basicConfig(level=logging.INFO)

# Gemini AI sozlash
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash-latest')

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- 2. TAQDIMOT YARATISH FUNKSIYASI ---
def create_presentation(content_text):
    # Gemini AI'dan kelgan matnni slaydga bo'lish (Misol uchun: "Slide X: Title\nText" ko'rinishida)
    prs = Presentation()
    
    # Slayd rejasini tozalash (masalan, ortiqcha harf va raqamlarni olib tashlash)
    slides = re.split(r'Slide \d+:\s*', content_text.replace('\n\n', '\n'))
    
    # Birinchi bo'sh slaydni tashlab yuboramiz
    if slides[0] == "": slides = slides[1:]

    for slide_data in slides:
        # Har bir slaydning nomi va matnini bo'lish
        lines = slide_data.strip().split('\n')
        if not lines: continue

        title_text = lines[0]
        body_text = "\n".join(lines[1:]) if len(lines) > 1 else ""

        # Slayd yaratish (1 - Title and Content layout)
        slide_layout = prs.slide_layouts[1] 
        slide = prs.slides.add_slide(slide_layout)
        
        # Slaydga nom va matn qo'shish
        slide.shapes.title.text = title_text
        if body_text:
            slide.placeholders[1].text = body_text

    # Taqdimotni xotirada (in-memory buffer) saqlash
    pptx_file = io.BytesIO()
    prs.save(pptx_file)
    pptx_file.seek(0)
    return pptx_file

# --- 3. BUYRUQLAR ---
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("Taqdimot yaratadigan botga xush kelibsiz! 👋\nMavzu yuboring, men taqdimot fayli yaratib beraman.")

@dp.message(F.text)
async def ai_presentation_handler(message: types.Message):
    await message.answer(f"'{message.text}' mavzusida taqdimot rejasi tayyorlanmoqda... ⏳")
    
    try:
        # 1. Gemini AI orqali taqdimot rejasi va matnlarini yaratish
        prompt = f"Create a structured presentation plan with slide titles and body text for {message.text}. Provide the output as 'Slide X: Title\\nText' for each slide. Make it 5 slides."
        response = model.generate_content(prompt)
        ai_content = response.text
        
        # 2. PowerPoint fayl yaratish (xotirada)
        await message.answer(f"AI javob berdi! PowerPoint fayliga joylanmoqda... 💾")
        pptx_buffer = create_presentation(ai_content)
        
        # 3. Faylni foydalanuvchiga yuborish
        file_input = types.BufferedInputFile(pptx_buffer.read(), filename=f"presentation_{message.text[:20]}.pptx")
        await message.answer_document(file_input, caption=f"'{message.text}' mavzusidagi taqdimot tayyor! ✅")
        
    except Exception as e:
        logging.error(f"Xato yuz berdi: {e}")
        await message.answer(f"Kechirasiz, taqdimot yaratishda xato yuz berdi: {str(e)[:50]}.")

# --- 4. ASOSIY QISM ---
async def main():
    # Eski ulanishlarni tozalash (Conflict)
    await bot.delete_webhook(drop_pending_updates=True)
    
    print("Bot taqdimot rejimi bilan pollingni boshladi...")
    
    # Botni ishga tushirish
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
