import os
import asyncio
import logging
import io
import google.generativeai as genai
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from pptx import Presentation
from pptx.util import Pt

# 1. SOZLAMALAR
TOKEN = "8128500951:AAFsgE6uq8eX2kY8_yxFnCLajzrEE3p7EtY"
GEMINI_API_KEY = os.getenv("GEMINI_KEY")

logging.basicConfig(level=logging.INFO)

# Gemini API ni sozlash
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    # Eng barqaror model nomidan foydalanamiz
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None

bot = Bot(token=TOKEN)
dp = Dispatcher()

# 2. TAQDIMOT YARATISH FUNKSIYASI (SAHIFALARGA BO'LISH BILAN)
def create_pptx(text_content, topic):
    prs = Presentation()
    
    # Matnni '###' belgisi orqali slayd bo'laklariga bo'lamiz
    slides_data = text_content.split("###")
    
    for content in slides_data:
        content = content.strip()
        if not content or len(content) < 10:
            continue
            
        # Slayd qo'shish (Sarlavha va matnli layout)
        slide_layout = prs.slide_layouts[1]
        slide = prs.slides.add_slide(slide_layout)
        
        # Sarlavha va matnni ajratish
        lines = content.split('\n')
        title_text = lines[0].replace("Slayd:", "").replace("Slayd", "").strip()
        body_text = "\n".join(lines[1:]).strip()
        
        # Slaydga yozish
        slide.shapes.title.text = title_text
        
        body_shape = slide.placeholders[1]
        body_shape.text = body_text
        
        # Shrift o'lchamini biroz kattalashtiramiz
        for paragraph in body_shape.text_frame.paragraphs:
            paragraph.font.size = Pt(18)
            
    buffer = io.BytesIO()
    prs.save(buffer)
    buffer.seek(0)
    return buffer

# 3. BOT KOMANDALARI
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        f"Assalomu alaykum, {message.from_user.first_name}!\n\n"
        "Menga mavzu yuboring, men sizga o'zbek tilida, sahifalangan taqdimot tayyorlab beraman. 📊"
    )

@dp.message(F.text)
async def handle_ppt_request(message: types.Message):
    if not model:
        await message.answer("Xato: GEMINI_KEY o'rnatilmagan yoki noto'g'ri. ❌")
        return

    wait_msg = await message.answer(f"🔍 '{message.text}' mavzusida taqdimot tayyorlanmoqda... ⏳")
    
    try:
        # Gemini uchun o'zbekcha buyruq
        prompt = (
            f"Mavzu: {message.text}. Ushbu mavzuda 5-6 ta slayddan iborat o'zbekcha taqdimot rejasi tuzing. "
            f"Juda muhim: Har bir slaydning boshlanishiga '###' belgisini qo'ying. "
            f"Faqat o'zbek tilida yozing."
        )
        
        response = model.generate_content(prompt)
        text_content = response.text

        # Faylni yaratish
        pptx_file = create_pptx(text_content, message.text)
        
        # Faylni Telegramga yuborish
        document = types.BufferedInputFile(
            pptx_file.read(), 
            filename=f"{message.text.replace(' ', '_')}_taqdimot.pptx"
        )
        
        await message.answer_document(document, caption=f"✅ '{message.text}' mavzusidagi taqdimot tayyor!")
        await wait_msg.delete()
        
    except Exception as e:
        logging.error(f"Xatolik: {e}")
        await message.answer("Kechirasiz, taqdimot yaratishda xatolik yuz berdi. 😔")

# 4. ISHGA TUSHIRISH
async def main():
    logging.info("Bot ishga tushdi...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
