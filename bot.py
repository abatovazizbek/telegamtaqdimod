import os
import asyncio
import google.generativeai as genai
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from pptx import Presentation

# 1. Railway Variables-dan nomlarni to'g'ri chaqirish
# DIQQAT: Railway'da qanday yozilgan bo'lsa, xuddi shunday bo'lishi shart!
BOT_TOKEN = os.getenv("8128500951:AAFsgE6uq8eX2kY8_yxFnCLajzrEE3p7EtY")  # Skrinshotda shunday yozilgan
GEMINI_KEY = os.getenv("AIzaSyDMFlvMD-VMDkOeNitUzBjSzNy1a3L2Xj0")

# 2. Gemini-ni sozlash
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    print("XATO: GEMINI_API_KEY topilmadi!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def create_pptx(ai_text, user_id):
    prs = Presentation()
    # Matnni slaydlar bo'yicha ajratish
    slides_data = ai_text.split("Slayd")
    for section in slides_data:
        if len(section.strip()) > 5:
            slide = prs.slides.add_slide(prs.slide_layouts[1])
            lines = section.strip().split('\n')
            slide.shapes.title.text = lines[0].replace(":", "").strip()
            slide.placeholders[1].text = "\n".join(lines[1:]).strip()
    
    file_path = f"pres_{user_id}.pptx"
    prs.save(file_path)
    return file_path

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Salom! Menga biror mavzu yozing, men Gemini AI yordamida taqdimot tayyorlab beraman.")

@dp.message(F.text)
async def handle_text(message: types.Message):
    if not GEMINI_KEY:
        await message.answer("Xatolik: API kalit topilmadi. Railway sozlamalarini tekshiring.")
        return

    wait_msg = await message.answer("⏳ Gemini o'ylamoqda...")
    
    try:
        # Gemini-dan matn so'rash
        prompt = f"'{message.text}' mavzusida 5 ta slayddan iborat taqdimot matnini o'zbek tilida yozib ber. Har bir slaydni 'Slayd: Sarlavha' shaklida boshla."
        response = model.generate_content(prompt)
        
        await wait_msg.edit_text("📄 PPTX fayl yaratilmoqda...")
        
        file_path = create_pptx(response.text, message.from_user.id)
        
        # Faylni yuborish
        await message.answer_document(types.FSInputFile(file_path), caption="Tayyor! ✅")
        os.remove(file_path)
        
    except Exception as e:
        # Xatoni aniq ko'rsatish
        await message.answer(f"❌ Xatolik yuz berdi: {str(e)[:100]}")
    finally:
        await wait_msg.delete()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
