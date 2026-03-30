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

# 2. MODELNI AVTOMATIK TANLASH (404 xatosini oldini olish uchun)
def get_working_model():
    if not GEMINI_API_KEY:
        return None
    genai.configure(api_key=GEMINI_API_KEY)
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for m_name in available_models:
            if 'gemini-1.5-flash' in m_name:
                return genai.GenerativeModel(m_name)
        return genai.GenerativeModel(available_models[0]) if available_models else None
    except Exception:
        return genai.GenerativeModel('gemini-1.5-flash')

model = get_working_model()

# 3. TAQDIMOT YARATISH (FILTR VA TOZALASH BILAN)
def create_pptx(text_content):
    prs = Presentation()
    
    # Matnni '###' orqali slaydlararo bo'lamiz
    slides_data = text_content.split("###")
    
    for content in slides_data:
        content = content.strip()
        
        # FILTR: Kirish so'zlarini yoki keraksiz qisqa matnlarni tashlab ketish
        if not content or len(content) < 15 or "so'ragan" in content.lower() or "reja" in content.lower()[:20]:
            continue
            
        slide_layout = prs.slide_layouts[1] # Sarlavha va matnli layout
        slide = prs.slides.add_slide(slide_layout)
        
        lines = content.split('\n')
        # Sarlavhadan yulduzcha va ortiqcha so'zlarni tozalash
        raw_title = lines[0].replace("Slayd:", "").replace("Slayd", "").replace("**", "").replace("*", "").strip()
        
        title = slide.shapes.title
        title.text = raw_title
        title.text_frame.paragraphs[0].font.color.rgb = RGBColor(0, 51, 102) # To'q ko'k rang

        body_shape = slide.placeholders[1]
        tf = body_shape.text_frame
        tf.word_wrap = True
        
        first_line = True
        for line in lines[1:]:
            clean_line = line.strip()
            if not clean_line or clean_line == "---":
                continue
            
            # Matn ichidagi yulduzcha va chiziqchalarni tozalash
            clean_line = clean_line.replace("**", "").replace("* ", "").replace("*", "").replace("- ", "")
            
            if first_line:
                p = tf.paragraphs[0]
                first_line = False
            else:
                p = tf.add_paragraph()
            
            p.text = clean_line
            p.font.size = Pt(18) # 20 tagacha slayd uchun mos shrift o'lchami
            p.font.color.rgb = RGBColor(0, 0, 0) # Qora rang
            
    buffer = io.BytesIO()
    prs.save(buffer)
    buffer.seek(0)
    return buffer

# 4. BOT KOMANDALARI
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        f"Assalomu alaykum, {message.from_user.first_name}!\n\n"
        "Mavzu yuboring, men faqat toza slaydli (20 tagacha) taqdimot tayyorlayman. ✨"
    )

@dp.message(F.text)
async def handle_ppt_request(message: types.Message):
    if not model:
        await message.answer("AI ulanishida xatolik yuz berdi. ❌")
        return

    wait_msg = await message.answer(f"🔍 '{message.text}' bo'yicha professional taqdimot tayyorlanmoqda... ⏳")
    
    try:
        # AI-ga qat'iy buyruq: faqat slaydlar mazmunini yozish
        prompt = (
            f"Mavzu: {message.text}. Ushbu mavzuda 15 tadan 20 tagacha slayddan iborat o'zbekcha taqdimot rejasi tuzing. "
            f"DIQQAT: Javobni darhol '###' belgisi bilan boshlang. Hech qanday kirish so'zlari (masalan: 'Mana reja') yozmang! "
            f"Faqat slayd sarlavhalari va mazmunini yozing. Har bir yangi slaydni '###' bilan boshlang. "
            f"Matn ichida hech qanday yulduzcha (* yoki **) ishlatmang."
        )
        
        response = model.generate_content(prompt)
        pptx_file = create_pptx(response.text)
        
        document = types.BufferedInputFile(pptx_file.read(), filename=f"{message.text.replace(' ', '_')}.pptx")
        await message.answer_document(document, caption=f"✅ '{message.text}' mavzusidagi taqdimot tayyorlandi!")
        await wait_msg.delete()
        
    except Exception as e:
        logging.error(f"Xatolik: {e}")
        await message.answer("Kechirasiz, taqdimot yaratishda xatolik yuz berdi. Qayta urinib ko'ring.")

# 5. ISHGA TUSHIRISH
async def main():
    # Telegram Conflict xatosini oldini olish uchun
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
