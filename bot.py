import os
import asyncio
import logging
import io
import re
import google.generativeai as genai
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from pptx import Presentation
from pptx.util import Pt
from pptx.dml.color import RGBColor

# 1. SOZLAMALAR
TOKEN = "8128500951:AAFsgE6uq8eX2kY8_yxFnCLajzrEE3p7EtY"
GEMINI_API_KEY = os.getenv("GEMINI_KEY")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Modelni sozlash
def get_working_model():
    if not GEMINI_API_KEY:
        logging.error("GEMINI_KEY topilmadi!")
        return None
    genai.configure(api_key=GEMINI_API_KEY)
    try:
        # Mavjud modellarni tekshirish
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for m_name in available_models:
            if 'gemini-1.5-flash' in m_name:
                return genai.GenerativeModel(m_name)
        return genai.GenerativeModel(available_models[0]) if available_models else None
    except Exception as e:
        logging.error(f"Model aniqlashda xato: {e}")
        return genai.GenerativeModel('gemini-1.5-flash')

model = get_working_model()

# 2. TAQDIMOT YARATISH (SAHIFALASHNI KUCHAYTIRILGAN VARIANTI)
def create_pptx(text_content):
    prs = Presentation()
    
    # Sahifalarga ajratish: ### yoki Slayd 1:, Slayd 2: kabi belgilardan foydalanamiz
    # Bu qism matnni qismlarga bo'lishni kafolatlaydi
    raw_slides = re.split(r'###|Slayd\s*\d+:|Slayd\s*\d+\.', text_content)
    
    for content in raw_slides:
        content = content.strip()
        # Agar matn juda qisqa bo'lsa yoki kirish gap bo'lsa tashlab ketamiz
        if not content or len(content) < 20 or "so'ragan" in content.lower():
            continue
            
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        lines = content.split('\n')
        
        # Sarlavhani tozalash va o'rnatish
        title_text = lines[0].replace("**", "").replace("*", "").strip()
        slide.shapes.title.text = title_text[:100] # Juda uzun bo'lib ketmasligi uchun
        
        tf = slide.placeholders[1].text_frame
        tf.word_wrap = True
        
        first_line = True
        for line in lines[1:]:
            clean_line = line.strip().replace("**", "").replace("* ", "").replace("*", "").replace("- ", "")
            if not clean_line or clean_line == "---": continue
            
            p = tf.paragraphs[0] if first_line else tf.add_paragraph()
            first_line = False
            p.text = clean_line
            p.font.size = Pt(18)
    
    buffer = io.BytesIO()
    prs.save(buffer)
    buffer.seek(0)
    return buffer

# 3. HANDLER
@dp.message(F.text)
async def handle_ppt_request(message: types.Message):
    # Sonni va mavzuni ajratish
    match = re.search(r'(\d+)', message.text)
    slide_count = int(match.group(1)) if match else 10
    clean_topic = re.sub(r'\d+\s*(ta|varaq|bet|slayd|slayid|sahifa)?', '', message.text, flags=re.IGNORECASE).strip()
    
    if not clean_topic: clean_topic = "Taqdimot"
    if slide_count > 25: slide_count = 25

    wait_msg = await message.answer(f"⏳ '{clean_topic}' mavzusida {slide_count} ta sahifali taqdimot tayyorlanmoqda...")
    
    try:
        # AI-ga sahifalash haqida juda qat'iy buyruq beramiz
        prompt = (
            f"Mavzu: {clean_topic}. Ushbu mavzuda aynan {slide_count} ta alohida slayddan iborat taqdimot rejasi yozing. "
            f"HAR BIR yangi slaydni '###' belgisi bilan boshlang. Bu juda muhim! "
            f"Hech qanday kirish so'zlari yozmang. Faqat slaydlar mazmuni bo'lsin. "
            f"Har bir slayd sarlavhasi qisqa bo'lsin."
        )
        
        response = model.generate_content(prompt)
        pptx_file = create_pptx(response.text)
        
        filename = f"{clean_topic.replace(' ', '_')}.pptx"
        document = types.BufferedInputFile(pptx_file.read(), filename=filename)
        
        await message.answer_document(document, caption=f"✅ {slide_count} ta sahifaga ajratilgan taqdimot tayyor!")
        await wait_msg.delete()
        
    except Exception as e:
        logging.error(f"Xato: {e}")
        await message.answer("Xatolik yuz berdi. Qayta urinib ko'ring.")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
