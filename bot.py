import os
import asyncio
import logging
import io
import google.generativeai as genai
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from pptx import Presentation
from pptx.util import Inches, Pt

# 1. SOZLAMALAR
TOKEN = "8128500951:AAFsgE6uq8eX2kY8_yxFnCLajzrEE3p7EtY"
GEMINI_API_KEY = os.getenv("GEMINI_KEY")

logging.basicConfig(level=logging.INFO)
genai.configure(api_key=GEMINI_API_KEY)

# Modelni tanlash
model = genai.GenerativeModel('gemini-1.5-flash')

bot = Bot(token=TOKEN)
dp = Dispatcher()

# 2. TAQDIMOT YARATISH FUNKSIYASI
def create_pptx(text_content, topic):
    prs = Presentation()
    
    # Matnni '###' belgisi orqali slayd bo'laklariga bo'lamiz
    slides_content = text_content.split("###")
    
    for content in slides_content:
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
        
        # Slaydga matnlarni joylashtirish
        slide.shapes.title.text = title_text
        slide.placeholders[1].text = body_text
            
    buffer = io.BytesIO()
    prs.save(buffer)
    buffer.seek(0)
    return buffer

# 3. BOT KOMANDALARI
@dp.message(Command("start"))
async def start(message: types.Message):
    user_name = message.from_user.first_name
    await message.answer(
        f"Assalomu alaykum, {user_name}!\n\n"
        "Men sizga istalgan mavzuda **o'zbekcha taqdimot** tayyorlab beraman.\n"
        "Mavzuni yuboring:"
    )

@dp.message(F.text)
async def handle_ppt(message: types.Message):
    if not GEMINI_API_KEY:
        await message.answer("Xato: Railway Variables'da GEMINI_KEY topilmadi.")
        return

    wait_msg = await message.answer(f"🔍 '{message.text}' mavzusida ma'lumot yig'ilmoqda va taqdimot yaratilmoqda. Iltimos, kuting... ⏳")
    
    try:
        # Gemini uchun mukammal o'zbekcha prompt
        prompt = (
            f"Mavzu: {message.text}. Ushbu mavzuda 5-6 slayddan iborat mukammal o'zbekcha taqdimot rejasi tuzing. "
            f"Har bir yangi slaydni '###' belgisi bilan boshlang. "
            f"Faqat o'zbek tilida yozing. Har bir slayd sarlavhasi qisqa va mazmunli bo'lsin."
        )
        
        response = model.generate_content(prompt)
        text_content = response.text

        # Taqdimot faylini yaratish
        file_buffer = create_pptx(text_content, message.text)
        
        # Faylni yuborish
        document = types.BufferedInputFile(
            file_buffer.read(), 
            filename=f"{message.text.replace(' ', '_')}_taqdimot.pptx"
        )
        
        await message.answer_document(
            document, 
            caption=f"✅ '{message.text}' mavzusidagi taqdimot tayyorlandi!\n\n@SizningBotNominiYozing"
        )
        await wait_msg.delete()
        
    except Exception as e:
        logging.error(f"Xato yuz berdi: {e}")
        await message.answer("Kechirasiz, taqdimot yaratish jarayonida xato yuz berdi. Birozdan so'ng qayta urinib ko'ring.")

# 4. ISHGA TUSHIRISH
async def main():
    logging.info("Bot ishga tushdi...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
