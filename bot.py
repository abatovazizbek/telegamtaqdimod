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

# Model sozlamalari
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# 2. TAQDIMOT YARATISH
def create_pptx(text_content):
    prs = Presentation()
    # Matnni '###' orqali bo'lamiz
    slides_data = text_content.split("###")
    
    for content in slides_data:
        content = content.strip()
        # Kirish so'zlarini yoki qisqa keraksiz gaplarni tashlab ketamiz
        if not content or len(content) < 15 or any(x in content.lower()[:30] for x in ["so'ragan", "reja"]):
            continue
            
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        lines = content.split('\n')
        
        # Sarlavhadan barcha yulduzcha va keraksiz belgilarni tozalash
        title_text = lines[0].replace("Slayd:", "").replace("**", "").replace("*", "").strip()
        slide.shapes.title.text = title_text
        
        tf = slide.placeholders[1].text_frame
        tf.word_wrap = True
        
        first_line = True
        for line in lines[1:]:
            clean_line = line.strip().replace("**", "").replace("* ", "").replace("*", "").replace("- ", "")
            if not clean_line: continue
            
            p = tf.paragraphs[0] if first_line else tf.add_paragraph()
            first_line = False
            p.text = clean_line
            p.font.size = Pt(18)
    
    buffer = io.BytesIO()
    prs.save(buffer)
    buffer.seek(0)
    return buffer

# 3. MATNNI AJRATISH VA ISHLOV BERISH (ASOSIY QISM)
@dp.message(F.text)
async def handle_ppt_request(message: types.Message):
    user_text = message.text
    
    # 1. Raqamni (slayd sonini) qidirib topamiz
    match = re.search(r'(\d+)', user_text)
    if match:
        slide_count = int(match.group(1))
        # 2. Mavzuni tozalaymiz: sonni va "ta slayd/varaq" kabi so'zlarni o'chiramiz
        # Shunda "O'zbekiston 10 ta slayd" -> faqat "O'zbekiston" qoladi
        clean_topic = re.sub(r'\d+\s*(ta|varaq|bet|slayd|slayid|sahifa)?', '', user_text, flags=re.IGNORECASE).strip()
    else:
        slide_count = 10 # Agar son yozilmasa standart 10 ta
        clean_topic = user_text.strip()

    if not clean_topic: clean_topic = "Taqdimot"
    if slide_count > 25: slide_count = 25 # Limit

    wait_msg = await message.answer(f"🔍 '{clean_topic}' mavzusida {slide_count} ta slayd tayyorlanmoqda... ⏳")
    
    try:
        # Promptga faqat tozalangan mavzuni va aniq sonni yuboramiz
        prompt = (
            f"Mavzu: {clean_topic}. Ushbu mavzuda aynan {slide_count} ta slayddan iborat o'zbekcha taqdimot rejasi tuzing. "
            f"DIQQAT: Javobni faqat '###' belgisi bilan boshlang. Hech qanday kirish so'zlari yozmang. "
            f"Slayd sarlavhalarida '{slide_count} ta slayd' degan iborani ishlatmang!"
        )
        
        response = model.generate_content(prompt)
        pptx_file = create_pptx(response.text)
        
        # Fayl nomida ham faqat mavzu bo'ladi
        filename = f"{clean_topic.replace(' ', '_')}.pptx"
        document = types.BufferedInputFile(pptx_file.read(), filename=filename)
        
        await message.answer_document(document, caption=f"✅ '{clean_topic}' bo'yicha {slide_count} ta slayd tayyor!")
        await wait_msg.delete()
        
    except Exception as e:
        logging.error(f"Xatolik: {e}")
        await message.answer("Xatolik yuz berdi, qayta urinib ko'ring.")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
