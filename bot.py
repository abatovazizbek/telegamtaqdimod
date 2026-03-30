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

# 2. MODELNI TO'G'RI SOZLASH (404 XATOSI UCHUN)
# Loglardagi '404 models/gemini-1.5-flash is not found' xatosini oldini oladi
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

# 3. TAQDIMOT YARATISH (YULDUZCHALAR VA KIRISH SO'ZLARISIZ)
# Slaydlardagi yulduzcha (*) va (**) belgilarini tozalaydi
def create_pptx(text_content):
    prs = Presentation()
    slides_data = text_content.split("###")
    
    for content in slides_data:
        content = content.strip()
        # "Mana siz so'ragan reja" kabi kirish gaplarini slaydlarga qo'shmaydi
        if not content or len(content) < 15 or any(x in content.lower()[:40] for x in ["so'ragan", "reja", "assalom"]):
            continue
            
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        lines = content.split('\n')
        
        # Sarlavhani tozalash
        title_text = lines[0].replace("Slayd:", "").replace("**", "").replace("*", "").strip()
        slide.shapes.title.text = title_text
        slide.shapes.title.text_frame.paragraphs[0].font.color.rgb = RGBColor(0, 51, 102)

        tf = slide.placeholders[1].text_frame
        tf.word_wrap = True
        
        first_line = True
        for line in lines[1:]:
            # Matn ichidagi barcha yulduzchalarni o'chiradi
            clean_line = line.strip().replace("**", "").replace("* ", "").replace("*", "").replace("- ", "")
            if not clean_line or clean_line == "---": continue
            
            p = tf.paragraphs[0] if first_line else tf.add_paragraph()
            first_line = False
            p.text = clean_line
            p.font.size = Pt(18)
            p.font.color.rgb = RGBColor(0, 0, 0)
            
    buffer = io.BytesIO()
    prs.save(buffer)
    buffer.seek(0)
    return buffer

# 4. MATNNI TAHLIL QILISH (SLAYDLAR SONIGA MOSLASHISH)
# Foydalanuvchi yozgan sondan miqdorni, matndan esa mavzuni ajratadi
@dp.message(F.text)
async def handle_ppt_request(message: types.Message):
    if not model:
        await message.answer("AI ulanishida xatolik yuz berdi! ❌")
        return

    # Matn ichidan sonni topish
    match = re.search(r'(\d+)', message.text)
    if match:
        slide_count = int(match.group(1))
        # Mavzudan sonni olib tashlaydi, shunda u sarlavhaga qo'shilmaydi
        clean_topic = re.sub(r'\d+\s*(ta|varaq|bet|slayd|slayid|sahifa)?', '', message.text, flags=re.IGNORECASE).strip()
    else:
        slide_count = 10
        clean_topic = message.text.strip()

    if not clean_topic: clean_topic = "Taqdimot"
    if slide_count > 25: slide_count = 25

    wait_msg = await message.answer(f"🔍 '{clean_topic}' mavzusida {slide_count} ta slayd tayyorlanmoqda... ⏳")
    
    try:
        prompt = (
            f"Mavzu: {clean_topic}. Ushbu mavzuda aynan {slide_count} ta slayddan iborat o'zbekcha taqdimot rejasi tuzing. "
            f"DIQQAT: Javobni darhol '###' belgisi bilan boshlang. Hech qanday kirish so'zlari yozmang! "
            f"Slaydlar ichida yulduzcha (* yoki **) ishlatmang."
        )
        
        response = model.generate_content(prompt)
        pptx_file = create_pptx(response.text)
        
        filename = f"{clean_topic.replace(' ', '_')}.pptx"
        document = types.BufferedInputFile(pptx_file.read(), filename=filename)
        
        await message.answer_document(document, caption=f"✅ '{clean_topic}' bo'yicha {slide_count} ta slayd tayyor!")
        await wait_msg.delete()
        
    except Exception as e:
        logging.error(f"Xatolik: {e}")
        await message.answer("Xatolik yuz berdi, qayta urinib ko'ring.")

# 5. ISHGA TUSHIRISH (CONFLICT XATOSI UCHUN)
async def main():
    # 'TelegramConflictError' xatosini oldini oladi
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
