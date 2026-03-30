import os
import asyncio
import logging
import io
import re
import google.generativeai as genai
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

# 1. SOZLAMALAR
TOKEN = "8128500951:AAFsgE6uq8eX2kY8_yxFnCLajzrEE3p7EtY"
GEMINI_API_KEY = os.getenv("GEMINI_KEY")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# 2. MODELNI AVTOMATIK TANLASH (Adaptive Selection)
def get_working_model():
    if not GEMINI_API_KEY:
        return None
    genai.configure(api_key=GEMINI_API_KEY)
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for m_name in available_models:
            if 'gemini-1.5-flash' in m_name:
                return genai.GenerativeModel(m_name)
        return genai.GenerativeModel(available_models[0]) if available_models else None
    except Exception:
        return genai.GenerativeModel('gemini-1.5-flash')

model = get_working_model()

# 3. TAQDIMOT YARATISH (TOZALASH VA FILTR BILAN)
def create_pptx(text_content):
    prs = Presentation()
    slides_data = text_content.split("###")
    
    for content in slides_data:
        content = content.strip()
        
        # Kirish so'zlarini filtrlash (Oldingi xatolar tuzatildi)
        if not content or len(content) < 15 or any(word in content.lower()[:30] for word in ["so'ragan", "reja", "assalom"]):
            continue
            
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        lines = content.split('\n')
        
        # Sarlavhadan yulduzcha va ortiqcha belgilarni tozalash
        raw_title = lines[0].replace("Slayd:", "").replace("Slayd", "").replace("**", "").replace("*", "").strip()
        
        title_shape = slide.shapes.title
        title_shape.text = raw_title
        title_shape.text_frame.paragraphs[0].font.color.rgb = RGBColor(0, 51, 102)

        tf = slide.placeholders[1].text_frame
        tf.word_wrap = True
        
        first_line = True
        for line in lines[1:]:
            clean_line = line.strip().replace("**", "").replace("* ", "").replace("*", "").replace("- ", "")
            if not clean_line or clean_line == "---":
                continue
            
            p = tf.paragraphs[0] if first_line else tf.add_paragraph()
            first_line = False
            p.text = clean_line
            p.font.size = Pt(18)
            p.font.color.rgb = RGBColor(0, 0, 0)
            
    buffer = io.BytesIO()
    prs.save(buffer)
    buffer.seek(0)
    return buffer

# 4. BOT HANDLERLARI
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        f"Assalomu alaykum, {message.from_user.first_name}!\n\n"
        "Menga mavzu va slaydlar sonini yozing. Masalan:\n"
        "👉 'O'zbekiston tarixi 10 ta slayd'\n"
        "👉 'Sun'iy intellekt 20 varaq'"
    )

@dp.message(F.text)
async def handle_ppt_request(message: types.Message):
    if not model:
        await message.answer("AI ulanishida xatolik! ❌")
        return

    # Matn ichidan sonni qidirib topish (Regex)
    numbers = re.findall(r'\d+', message.text)
    slide_count = int(numbers[0]) if numbers else 10 # Agar son yozilmasa, standart 10 ta
    
    # Maksimal 25 tagacha cheklaymiz (AI limiti uchun)
    if slide_count > 25: slide_count = 25
    if slide_count < 1: slide_count = 5

    wait_msg = await message.answer(f"🔍 '{message.text}' mavzusida {slide_count} ta slayd tayyorlanmoqda... ⏳")
    
    try:
        # Promptni foydalanuvchi so'ragan songa moslash
        prompt = (
            f"Mavzu: {message.text}. Ushbu mavzuda aynan {slide_count} ta slayddan iborat o'zbekcha taqdimot rejasi tuzing. "
            f"DIQQAT: Javobni darhol '###' belgisi bilan boshlang. Kirish so'zlari kerak emas! "
            f"Har bir yangi slayd sarlavhasini '###' bilan boshlang. Matnda yulduzcha (* yoki **) ishlatmang."
        )
        
        response = model.generate_content(prompt)
        pptx_file = create_pptx(response.text)
        
        filename = f"{message.text[:20].replace(' ', '_')}.pptx"
        document = types.BufferedInputFile(pptx_file.read(), filename=filename)
        
        await message.answer_document(document, caption=f"✅ {slide_count} ta slayddan iborat taqdimot tayyor!")
        await wait_msg.delete()
        
    except Exception as e:
        logging.error(f"Xatolik: {e}")
        await message.answer("Xatolik bo'ldi. Iltimos, mavzuni qisqaroq yozib ko'ring.")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
