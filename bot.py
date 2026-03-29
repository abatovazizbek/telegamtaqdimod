import os
import asyncio
import google.generativeai as genai
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from pptx import Presentation

# 1. Railway Variables-dan ma'lumotlarni olish
# Skrinshotingizdagi nomlar bilan bir xil qilindi
TOKEN = os.environ.get("8128500951:AAFsgE6uq8eX2kY8_yxFnCLajzrEE3p7EtY")
GEMINI_KEY = os.environ.get("AIzaSyDMFlvMD-VMDkOeNitUzBjSzNy1a3L2Xj0")

# 2. Gemini AI-ni sozlash
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    print("XATO: GEMINI_API_KEY topilmadi!")

# 3. Botni ishga tushirish (Tokenni tekshirish bilan)
if not TOKEN:
    raise ValueError("XATO: TELEGRAM_TOKEN Railway-da topilmadi!")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Taqdimot yaratish funksiyasi
def create_pptx(ai_text, user_id):
    prs = Presentation()
    # Matnni slaydlar bo'yicha bo'lish (Gemini bergan formatga qarab)
    sections = ai_text.split("Slayd")
    
    for section in sections:
        if len(section.strip()) > 5:
            slide = prs.slides.add_slide(prs.slide_layouts[1])
            lines = section.strip().split('\n')
            # Sarlavha va matnni ajratish
            slide.shapes.title.text = lines[0].replace(":", "").strip()
            slide.placeholders[1].text = "\n".join(lines[1:]).strip()

    file_path = f"pres_{user_id}.pptx"
    prs.save(file_path)
    return file_path

# /start komandasi
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Salom! Men aqlli taqdimot botiman. 🎓\n\n"
                         "Menga mavzu yozib yuboring, men sizga PowerPoint fayl tayyorlab beraman.")

# Matnli xabarlarni qayta ishlash
@dp.message(F.text)
async def handle_text(message: types.Message):
    if not GEMINI_KEY:
        await message.answer("Xatolik: Gemini API kaliti ulanmagan.")
        return

    status_msg = await message.answer("⏳ Gemini ma'lumot tayyorlamoqda, kuting...")
    
    try:
        # Gemini-dan o'zbek tilida strukturali matn so'rash
        prompt = (f"'{message.text}' mavzusida 5 ta slayddan iborat taqdimot matnini o'zbek tilida yozib ber. "
                  f"Har bir slaydni 'Slayd: Sarlavha' so'zi bilan boshla.")
        
        response = model.generate_content(prompt)
        
        await status_msg.edit_text("📄 PowerPoint fayl shakllantirilmoqda...")
        
        # PPTX faylni yaratish
        file_path = create_pptx(response.text, message.from_user.id)
        
        # Faylni foydalanuvchiga yuborish
        await message.answer_document(
            types.FSInputFile(file_path), 
            caption=f"✅ '{message.text}' mavzusidagi taqdimotingiz tayyor!"
        )
        
        # Serverni tozalash
        os.remove(file_path)
        
    except Exception as e:
        await message.answer(f"❌ Xatolik yuz berdi: {str(e)[:100]}")
    finally:
        await status_msg.delete()

async def main():
    print("Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
