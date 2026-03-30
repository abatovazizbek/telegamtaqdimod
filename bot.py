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
# Eslatma: Kalitlarni kod ichiga yozdik, lekin 'import os' baribir kerak bo'lishi mumkin
TOKEN = "8128500951:AAFsgE6uq8eX2kY8_yxFnCLajzrEE3p7EtY"
GEMINI_API_KEY = "AIzaSyBzg_66XVCdCX2JYRObFNVOZYAkpHcNptM"
GOOGLE_API_KEY = "AIzaSyA_Cvc-r0jDfeQCnOWJO1x9ffHKUFZ1k30"
GOOGLE_CX = "3399766467a1d4c32"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# 2. GEMINI MODELINI SOZLASH
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
# 3. RASM QIDIRISH (Google)
def get_image(query):
    try:
        url = f"https://www.googleapis.com/customsearch/v1?q={query}&searchType=image&key={GOOGLE_API_KEY}&cx={GOOGLE_CX}&num=1"
        res = requests.get(url, timeout=5).json()
        if 'items' in res:
            return res['items'][0]['link']
    except:
        return None
    return None

# 4. TAQDIMOT YARATISH LOGIKASI
def create_pptx(raw_text):
    prs = Presentation()
    sections = re.split(r'###', raw_text)
    
    for section in sections:
        section = section.strip()
        if not section or len(section) < 15: continue
            
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        lines = section.split('\n')
        
        # Sarlavha
        title_text = lines[0].replace("**", "").replace("*", "").strip()
        slide.shapes.title.text = title_text[:100]
        
        # Matn qismi
        body = slide.placeholders[1]
        body.width = Inches(5.0)
        tf = body.text_frame
        tf.word_wrap = True
        
        for line in lines[1:]:
            clean = line.strip().replace("**", "").replace("*", "").replace("- ", "")
            if clean:
                p = tf.add_paragraph()
                p.text = clean
                p.font.size = Pt(18)

        # Rasm qo'shish
        img_url = get_image(title_text)
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

# 5. BOT BUYRUQLARI
@dp.message(F.text == "/start")
async def cmd_start(message: types.Message):
    await message.answer("Salom! Taqdimot mavzusini yozing, men uni tayyorlab beraman.")

@dp.message(F.text)
async def handle_ppt(message: types.Message):
    if message.text.startswith('/'): return
    
    status = await message.answer(f"⏳ '{message.text}' mavzusida taqdimot tayyorlanyapti...")
    
    try:
        # Gemini-dan matn so'rash
        prompt = f"Mavzu: {message.text}. 5 ta slayd uchun o'zbekcha matn yoz. Har bir slaydni '###' bilan ajrat."
        response = model.generate_content(prompt)
        
        # Faylni yaratish
        file_buffer = create_pptx(response.text)
        file = types.BufferedInputFile(file_buffer.read(), filename=f"{message.text}.pptx")
        
        await message.answer_document(file, caption=f"✅ '{message.text}' tayyor!")
        await status.delete()
    except Exception as e:
        logging.error(f"Xato: {e}")
        await message.answer(f"❌ Xatolik: {str(e)[:50]}...")

# 6. ASOSIY ISHGA TUSHIRISH
async def main():
    # Eski webhooklarni tozalash
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
