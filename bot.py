import os
import asyncio
import google.generativeai as genai
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from pptx import Presentation
import io

# 1. MA'LUMOTLAR
TOKEN = "8128500951:AAFsgE6uq8eX2kY8_yxFnCLajzrEE3p7EtY"
GEMINI_API_KEY = os.getenv("GEMINI_KEY") # Kalitni shu yerga qo'ying

genai.configure(api_key=GEMINI_API_KEY)

# --- MODELNI AVTOMATIK ANIQLASH ---
def get_working_model():
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    print(f"Ochiq modellar: {available_models}")
    
    # Eng yaxshi ko'rilgan modellar tartibi
    preferred = ['models/gemini-1.5-flash', 'models/gemini-1.0-pro', 'models/gemini-pro']
    for p in preferred:
        if p in available_models:
            return genai.GenerativeModel(p)
    
    # Agar hech biri bo'lmasa, birinchisini olamiz
    return genai.GenerativeModel(available_models[0]) if available_models else None

model = get_working_model()

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- TAQDIMOT YARATISH ---
def create_pptx(text_content, topic):
    prs = Presentation()
    # Oddiygina slaydlarga bo'lish
    slides_content = text_content.split("Slide")
    
    for content in slides_content:
        if len(content.strip()) < 5: continue
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        lines = content.strip().split('\n')
        slide.shapes.title.text = lines[0]
        if len(lines) > 1:
            slide.placeholders[1].text = "\n".join(lines[1:])
            
    buffer = io.BytesIO()
    prs.save(buffer)
    buffer.seek(0)
    return buffer

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Taqdimot bot tayyor! Mavzu yuboring.")

@dp.message(F.text)
async def handle_ppt(message: types.Message):
    if not model:
        await message.answer("Xato: Gemini modeli topilmadi. API keyni tekshiring.")
        return

    m = await message.answer("Taqdimot tayyorlanmoqda... ⏳")
    try:
        prompt = f"Create a 5-slide presentation about {message.text}. Format: Slide Title\nBullet points."
        response = model.generate_content(prompt)
        
        file_buffer = create_pptx(response.text, message.text)
        document = types.BufferedInputFile(file_buffer.read(), filename=f"{message.text}.pptx")
        
        await message.answer_document(document, caption="Tayyor! ✅")
        await m.delete()
    except Exception as e:
        await message.answer(f"Xato yuz berdi: {str(e)[:100]}")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
