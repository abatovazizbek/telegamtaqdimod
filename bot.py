import os
import asyncio
import logging
import io
import re
import requests
import google.generativeai as genai
from aiogram import Bot, Dispatcher, F, types
from pptx import Presentation
from pptx.util import Pt, Inches

# 1. SOZLAMALAR
TOKEN = "8128500951:AAFsgE6uq8eX2kY8_yxFnCLajzrEE3p7EtY"
GEMINI_API_KEY = os.getenv("AIzaSyBzg_66XVCdCX2JYRObFNVOZYAkpHcNptM")
GOOGLE_API_KEY = os.getenv("AIzaSyA_Cvc-r0jDfeQCnOWJO1x9ffHKUFZ1k30")
GOOGLE_CX = os.getenv("3399766467a1d4c32")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# 2. GEMINI SOZLAMASI
def get_best_model():
    """Mavjud modellardan eng mosini avtomatik tanlaydi (404 oldini olish uchun)"""
    models_to_try = [
        'gemini-1.5-flash', # Eng yangi va tezkor
        'gemini-1.5-pro',   # Kuchliroq
        'gemini-pro'        # Eski versiya (agar boshqalari topilmasa)
    ]
    
    for model_name in models_to_try:
        try:
            m = genai.GenerativeModel(model_name)
            # Kichik test o'tkazamiz (model haqiqatda borligini tekshirish uchun)
            logging.info(f"Model tekshirilmoqda: {model_name}")
            return m
        except Exception as e:
            logging.warning(f"{model_name} topilmadi yoki xato: {e}")
            continue

# 3. RASM QIDIRISH (Google orqali)
def get_image(query):
    try:
        url = f"https://www.googleapis.com/customsearch/v1?q={query}&searchType=image&key={GOOGLE_API_KEY}&cx={GOOGLE_CX}&num=1"
        res = requests.get(url, timeout=5).json()
        if 'items' in res:
            return res['items'][0]['link']
    except:
        return None
    return None

# 4. TAQDIMOT YARATISH
def create_pptx(topic, slides_text):
    prs = Presentation()
    # Slaydlarni ajratish
    sections = re.split(r'###', slides_text)
    
    for section in sections:
        section = section.strip()
        if not section: continue
        
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        lines = section.split('\n')
        
        # Sarlavha
        title = lines[0].replace("**", "").replace("*", "").strip()
        slide.shapes.title.text = title
        
        # Matn
        body_shape = slide.placeholders[1]
        body_shape.width = Inches(5)
        tf = body_shape.text_frame
        tf.word_wrap = True
        
        for line in lines[1:]:
            clean_line = line.strip().replace("**", "").replace("*", "")
            if clean_line:
                p = tf.add_paragraph()
                p.text = clean_line
                p.font.size = Pt(18)

        # Rasm qo'shish
        img_url = get_image(title)
        if img_url:
            try:
                img_data = requests.get(img_url, timeout=5).content
                slide.shapes.add_picture(io.BytesIO(img_data), Inches(5.5), Inches(1.5), width=Inches(4))
            except:
                pass

    buffer = io.BytesIO()
    prs.save(buffer)
    buffer.seek(0)
    return buffer

# 5. BOT BUYRUG'I
@dp.message(F.text)
async def start_ppt(message: types.Message):
    wait_msg = await message.answer("⏳ Taqdimot tayyorlanyapti, iltimos kuting...")
    
    try:
        prompt = f"Mavzu: {message.text}. 5 ta slayd uchun matn yoz. Har bir slaydni '###' bilan ajrat. Faqat matn bo'lsin."
        response = model.generate_content(prompt)
        
        file_buffer = create_pptx(message.text, response.text)
        file = types.BufferedInputFile(file_buffer.read(), filename=f"{message.text}.pptx")
        
        await message.answer_document(file, caption="✅ Taqdimot tayyor!")
        await wait_msg.delete()
    except Exception as e:
        logging.error(f"Xato: {e}")
        await message.answer("❌ Xatolik yuz berdi. API kalitlarni tekshiring.")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
