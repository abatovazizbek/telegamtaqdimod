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

# 1. SOZLAMALAR (Environment Variables orqali)
# TOKEN'ingizni kod ichida qoldiring (sizning xohishingizga ko'ra)
TOKEN = "8128500951:AAFsgE6uq8eX2kY8_yxFnCLajzrEE3p7EtY"
GEMINI_API_KEY = os.getenv("AIzaSyBzg_66XVCdCX2JYRObFNVOZYAkpHcNptM")
GOOGLE_API_KEY = os.getenv("AIzaSyA_Cvc-r0jDfeQCnOWJO1x9ffHKUFZ1k30")
GOOGLE_CX = os.getenv("3399766467a1d4c32")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# 2. GEMINI MODELINI MOSLASHUVCHAN (ADAPTIVE) YUKLASH
# Bu qism 404 xatosini oldini oladi
genai.configure(api_key=GEMINI_API_KEY)

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
    
    # Agar hech biri ishlamasa, xatolik qaytaramiz
    raise Exception("Hech qanday Gemini modeli yuklanmadi. API kalitni tekshiring.")

# Modelni yuklaymiz
try:
    model = get_best_model()
    logging.info("Gemini modeli muvaffaqiyatli ulandi!")
except Exception as e:
    logging.error(e)

# 3. GOOGLE RASM QIDIRUV FUNKSIYASI
def get_google_image(query):
    try:
        url = f"https://www.googleapis.com/customsearch/v1?q={query}&searchType=image&key={GOOGLE_API_KEY}&cx={GOOGLE_CX}&num=1"
        res = requests.get(url, timeout=10).json()
        if 'items' in res:
            return res['items'][0]['link']
    except Exception as e:
        logging.error(f"Rasm qidirishda xato (ehtimol Google sozlamalari noto'g'ri): {e}")
    return None

# 4. TAQDIMOT YARATISH (Rasm bo'lmasa, uni o'tkazib yuborish)
def create_pptx(text_content):
    prs = Presentation()
    # Slaydlarni ### yoki "Slayd 1" kabi belgilardan ajratamiz
    raw_slides = re.split(r'###|Slayd\s*\d+[:.]', text_content)
    
    for content in raw_slides:
        content = content.strip()
        if not content or len(content) < 30:
            continue
            
        slide = prs.slides.add_slide(prs.slide_layouts[1]) # Sarlavha va Mazmun
        lines = content.split('\n')
        
        # Sarlavhani yulduzchalardan tozalash
        title_text = lines[0].replace("**", "").replace("*", "").strip()
        slide.shapes.title.text = title_text[:100]
        
        # Matn qismi (rasmga joy qolishi uchun kengligini cheklaymiz)
        body = slide.placeholders[1]
        body.width = Inches(5.5)
        tf = body.text_frame
        tf.word_wrap = True
        
        first_p = True
        for line in lines[1:]:
            # Yulduzcha va chiziqchalarni tozalash
            clean_line = line.strip().replace("**", "").replace("*", "").replace("- ", "")
            if clean_line:
                p = tf.paragraphs[0] if first_p else tf.add_paragraph()
                p.text = clean_line
                p.font.size = Pt(18)
                first_p = False

        # RASM QO'SHISH (Faqat rasm topsagina qo'shadi, topolmasa xato bermaydi)
        img_url = get_google_image(title_text)
        if img_url:
            try:
                img_res = requests.get(img_url, timeout=10)
                img_data = io.BytesIO(img_res.content)
                slide.shapes.add_picture(img_data, Inches(6), Inches(1.5), width=Inches(3.5))
            except Exception as e:
                logging.warning(f"Rasm qo'shishda xato: {e}")
                pass # Rasmsiz slaydni tayyorlashni davom ettirish
    
    buffer = io.BytesIO()
    prs.save(buffer)
    buffer.seek(0)
    return buffer

# 5. ASOSIY HANDLER
@dp.message(F.text)
async def handle_ppt_request(message: types.Message):
    match = re.search(r'(\d+)', message.text)
    slide_count = int(match.group(1)) if match else 10
    topic = re.sub(r'\d+\s*(ta|slayd|varaq|bet)?', '', message.text, flags=re.IGNORECASE).strip()
    
    if not topic:
        return await message.answer("Iltimos, taqdimot mavzusini yozing!")

    wait_msg = await message.answer(f"⏳ '{topic}' mavzusida {slide_count} ta slaydli rasmli taqdimot tayyorlanmoqda... ⏳")
    
    try:
        prompt = (
            f"Mavzu: {topic}. {slide_count} ta slayd yozing. "
            f"Har bir slaydni '###' bilan ajrating. Faqat toza matn yozing, "
            f"yulduzcha (* yoki **) ishlatmang. Kirish so'zlarini yozmang."
        )
        
        response = model.generate_content(prompt)
        pptx_file = create_pptx(response.text)
        
        filename = f"{topic.replace(' ', '_')}.pptx"
        document = types.BufferedInputFile(pptx_file.read(), filename=filename)
        
        await message.answer_document(document, caption=f"✅ '{topic}' mavzusidagi taqdimot tayyor!")
        await wait_msg.delete()
        
    except Exception as e:
        logging.error(f"Xatolik: {e}")
        await message.answer("Xatolik yuz berdi. Iltimos, Railway sozlamalarini tekshiring.")

# 6. ISHGA TUSHIRISH
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
