import os
import asyncio
import logging
import io
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

# 2. MODELNI AVTOMATIK ANIQLASH (404 XATOSINI OLDINI OLISH)
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

# 3. TAQDIMOT YARATISH (YULDUZCHALARSIZ VA 20 TAgacha SLAYD)
def create_pptx(text_content):
    prs = Presentation()
    
    # Matnni '###' orqali slaydlararo bo'lamiz
    slides_data = text_content.split("###")
    
    for content in slides_data:
        content = content.strip()
        if not content or len(content) < 10:
            continue
            
        slide_layout = prs.slide_layouts[1] # Sarlavha va matn
        slide = prs.slides.add_slide(slide_layout)
        
        # Sarlavha va matnni ajratish
        lines = content.split('\n')
        # Sarlavhadan yulduzchalarni tozalash
        raw_title = lines[0].replace("Slayd:", "").replace("Slayd", "").replace("**", "").replace("*", "").strip()
        
        title = slide.shapes.title
        title.text = raw_title
        title.text_frame.paragraphs[0].font.color.rgb = RGBColor(0, 51, 102) # To'q ko'k

        body_shape = slide.placeholders[1]
        tf = body_shape.text_frame
        tf.word_wrap = True
        
        first_line = True
        for line in lines[1:]:
            clean_line = line.strip()
            if not clean_line or clean_line == "---":
                continue
            
            # MATNNI TOZALASH (Yulduzcha va chiziqchalarni olib tashlash)
            clean_line = clean_line.replace("**", "")
            if clean_line.startswith("* "): clean_line = clean_line[2:]
            elif clean_line.startswith("*"): clean_line = clean_line[1:]
            if clean_line.startswith("- "): clean_line = clean_line[2:]
            
            if first_line:
                p = tf.paragraphs[0]
                first_line = False
            else:
                p = tf.add_paragraph()
            
            p.text = clean_line
            p.font.size = Pt(18)
            p.font.color.rgb = RGBColor(0, 0, 0) # Qora rang
            
    buffer = io.BytesIO()
    prs.save(buffer)
    buffer.seek(0)
    return buffer

# 4. BOT HANDLERLARI
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("Assalomu alaykum! Mavzu yuboring, men sizga 20 tagacha slayddan iborat mukammal va toza taqdimot tayyorlayman. ✨")

@dp.message(F.text)
async def handle_ppt_request(message: types.Message):
    if not model:
        await message.answer("Xato: AI modeli ulanmagan. ❌")
        return

    wait_msg = await message.answer(f"🔍 '{message.text}' bo'yicha katta hajmdagi taqdimot tayyorlanmoqda (20 tagacha slayd). Iltimos, kuting... ⏳")
    
    try:
        # 20 ta slayd so'rash uchun PROMPT
        prompt = (
            f"Mavzu: {message.text}. Ushbu mavzuda kamida 15 ta, ko'pi bilan 20 ta slayddan iborat mukammal o'zbekcha taqdimot rejasi tuzing. "
            f"Har bir slaydni '###' belgisi bilan boshlang. Har bir slayd mazmuni boy va tushunarli bo'lsin. "
            f"Faqat o'zbek tilida yozing. Matn ichida ** yoki * belgilarini ishlatmang."
        )
        
        response = model.generate_content(prompt)
        pptx_file = create_pptx(response.text)
        
        document = types.BufferedInputFile(pptx_file.read(), filename=f"{message.text}.pptx")
        await message.answer_document(document, caption=f"✅ '{message.text}' mavzusida maxsus taqdimot tayyor!")
        await wait_msg.delete()
        
    except Exception as e:
        logging.error(f"Xatolik: {e}")
        await message.answer("Kechirasiz, juda katta hajmdagi ma'lumotni qayta ishlashda xatolik bo'ldi. Qayta urinib ko'ring.")

async def main():
    # Eski xabarlarni tozalash (Conflict xatosini oldini oladi)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
