import os
import asyncio
import google.generativeai as genai
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from pptx import Presentation

# Railway Variables - Skrinshotdagi nomlar bilan bir xil qilindi
BOT_TOKEN = os.environ.get("8128500951:AAFsgE6uq8eX2kY8_yxFnCLajzrEE3p7EtY")
API_KEY = os.environ.get("AIzaSyDMFlvMD-VMDkOeNitUzBjSzNy1a3L2Xj0")

# Gemini AI sozlash
if API_KEY:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    print("XATO: GEMINI_KEY topilmadi!")

# Botni ishga tushirish
if not BOT_TOKEN:
    raise ValueError("XATO: TOKEN Railway-da topilmadi!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def create_pptx(ai_text, user_id):
    prs = Presentation()
    sections = ai_text.split("Slayd")
    for section in sections:
        if len(section.strip()) > 5:
            slide = prs.slides.add_slide(prs.slide_layouts[1])
            lines = section.strip().split('\n')
            slide.shapes.title.text = lines[0].replace(":", "").strip()
            slide.placeholders[1].text = "\n".join(lines[1:]).strip()
    
    file_path = f"taqdimot_{user_id}.pptx"
    prs.save(file_path)
    return file_path

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Salom! Menga mavzu yozing, men PowerPoint taqdimot tayyorlayman. ✅")

@dp.message(F.text)
async def handle_text(message: types.Message):
    if not API_KEY:
        await message.answer("Xatolik: Gemini API kaliti ulanmagan.")
        return

    wait_msg = await message.answer("⏳ Gemini tayyorlamoqda, kuting...")
    
    try:
        prompt = f"'{message.text}' mavzusida 5 ta slayddan iborat taqdimot matni yoz. Har birini 'Slayd: Sarlavha' bilan boshla."
        response = model.generate_content(prompt)
        
        await wait_msg.edit_text("📄 Fayl yaratilmoqda...")
        file_path = create_pptx(response.text, message.from_user.id)
        
        await message.answer_document(types.FSInputFile(file_path), caption="Tayyor! ✅")
        os.remove(file_path)
    except Exception as e:
        await message.answer(f"❌ Xatolik: {str(e)[:50]}")
    finally:
        await wait_msg.delete()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
