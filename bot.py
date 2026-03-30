import os
import asyncio
import logging
import io
import google.generativeai as genai
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from pptx import Presentation
from pptx.util import Pt

# 1. SOZLAMALAR VA LOGGING
TOKEN = "8128500951:AAFsgE6uq8eX2kY8_yxFnCLajzrEE3p7EtY"
GEMINI_API_KEY = os.getenv("GEMINI_KEY")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# 2. MODELNI AVTOMATIK ANIQLASH (MOSLASHUVCHAN)
def get_working_model():
    if not GEMINI_API_KEY:
        logging.error("GEMINI_KEY topilmadi!")
        return None
    
    genai.configure(api_key=GEMINI_API_KEY)
    
    try:
        # Google'dan sizning kalitingiz uchun ochiq modellarni olish
        available_models = [
            m.name for m in genai.list_models() 
            if 'generateContent' in m.supported_generation_methods
        ]
        
        logging.info(f"Mavjud modellar: {available_models}")

        # 1-navbatda 'gemini-1.5-flash' ni qidiramiz
        for m_name in available_models:
            if 'gemini-1.5-flash' in m_name:
                logging.info(f"Tanlangan model: {m_name}")
                return genai.GenerativeModel(m_name)
        
        # Agar flash bo'lmasa, pro yoki birinchi uchraganini olamiz
        if available_models:
            logging.warning(f"Zaxira modeli tanlandi: {available_models[0]}")
            return genai.GenerativeModel(available_models[0])
            
    except Exception as e:
        logging.error(f"Modelni aniqlashda xato: {e}")
        # Eng oxirgi chora sifatida standart nom
        return genai.GenerativeModel('gemini-1.5-flash-latest')

# Modelni ishga tushirish
model = get_working_model()

# 3. TAQDIMOT YARATISH FUNKSIYASI
def create_pptx(text_content, topic):
    prs = Presentation()
    
    # Matnni '###' orqali bo'laklarga bo'lamiz
    slides_data = text_content.split("###")
    
    for content in slides_data:
        content = content.strip()
        if not content or len(content) < 10:
            continue
            
        slide_layout = prs.slide_layouts[1] # Sarlavha va matn
        slide = prs.slides.add_slide(slide_layout)
        
        # Sarlavha va matnni ajratish
        lines = content.split('\n')
        title_text = lines[0].replace("Slayd:", "").replace("Slayd", "").strip()
        body_text = "\n".join(lines[1:]).strip()
        
        # Slaydga yozish
        slide.shapes.title.text = title_text
        body_shape = slide.placeholders[1]
        body_shape.text = body_text
        
        # Shriftni sozlash
        for paragraph in body_shape.text_frame.paragraphs:
            paragraph.font.size = Pt(18)
            
    buffer = io.BytesIO()
    prs.save(buffer)
    buffer.seek(0)
    return buffer

# 4. BOT HANDLERLARI
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        f"Assalomu alaykum, {message.from_user.first_name}!\n\n"
        "Men avtomatik moslashuvchan AI botman. Istalgan mavzuni yozing, "
        "men sahifalarga bo'lingan o'zbekcha taqdimot tayyorlab beraman."
    )

@dp.message(F.text)
async def handle_ppt_request(message: types.Message):
    if not model:
        await message.answer("Xato: AI modeli bilan bog'lanish imkonsiz. ❌")
        return

    wait_msg = await message.answer(f"🔍 '{message.text}' mavzusi tahlil qilinmoqda... ⏳")
    
    try:
        prompt = (
            f"Mavzu: {message.text}. Ushbu mavzuda 5-6 ta slayddan iborat o'zbekcha taqdimot rejasi tuzing. "
            f"Har bir yangi slaydni '###' belgisi bilan boshlang. Faqat o'zbek tilida yozing."
        )
        
        # AI matn yaratadi
        response = model.generate_content(prompt)
        text_content = response.text

        # Faylni yaratish
        pptx_file = create_pptx(text_content, message.text)
        
        # Faylni yuborish
        document = types.BufferedInputFile(
            pptx_file.read(), 
            filename=f"{message.text.replace(' ', '_')}.pptx"
        )
        
        await message.answer_document(document, caption=f"✅ '{message.text}' mavzusidagi taqdimot tayyor!")
        await wait_msg.delete()
        
    except Exception as e:
        logging.error(f"Xatolik: {e}")
        await message.answer("Kechirasiz, taqdimot yaratishda kutilmagan xato yuz berdi. 😔")

# 5. ISHGA TUSHIRISH
async def main():
    logging.info("Bot polling rejimida ishga tushdi...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
