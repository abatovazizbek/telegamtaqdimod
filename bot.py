import os
import asyncio
import google.generativeai as genai
from aiogram import Bot, Dispatcher, F, types
from pptx import Presentation

# SOZLAMALAR
TELEGRAM_TOKEN = "8128500951:AAFsgE6uq8eX2kY8_yxFnCLajzrEE3p7EtY"
GEMINI_API_KEY = "AIzaSyDMFlvMD-VMDkOeNitUzBjSzNy1a3L2Xj0" # Shu yerga nusxalangan kodni qo'ying

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

def create_pptx(ai_text, user_id):
    prs = Presentation()
    # Gemini bergan matnni slaydlar bo'yicha ajratishga harakat qilamiz
    slides_data = ai_text.split("Slayd") 
    
    for section in slides_data:
        if len(section.strip()) > 5:
            slide = prs.slides.add_slide(prs.slide_layouts[1])
            lines = section.strip().split('\n')
            slide.shapes.title.text = lines[0].replace(":", "")
            slide.placeholders[1].text = "\n".join(lines[1:])

    file_path = f"presentation_{user_id}.pptx"
    prs.save(file_path)
    return file_path

@dp.message(F.text)
async def handle_message(message: types.Message):
    wait_msg = await message.answer("Gemini o'ylamoqda va taqdimot tayyorlamoqda...")
    
    try:
        # Geminidan matn olish (maxsus formatda so'raymiz)
        prompt = f"'{message.text}' mavzusida 5 ta slayddan iborat taqdimot matnini tayyorla. Har bir slaydni 'Slayd: Sarlavha' ko'rinishida boshla."
        response = model.generate_content(prompt)
        
        # PPTX yaratish
        file_path = create_pptx(response.text, message.from_user.id)
        
        # Yuborish
        await message.answer_document(types.FSInputFile(file_path), caption="Tayyor!")
        os.remove(file_path)
    except Exception as e:
        await message.answer("Xatolik bo'ldi, qaytadan urinib ko'ring.")
    finally:
        await wait_msg.delete()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
