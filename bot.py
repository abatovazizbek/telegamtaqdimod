import os
import asyncio
import logging
import io
import re
import requests
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from pptx import Presentation
from pptx.util import Pt, Inches
from pptx.dml.color import RGBColor

# ===================== YANGI GOOGLE GENAI =====================
from google import genai

# ===================== SOZLAMALAR =====================
TOKEN = "8128500951:AAFsgE6uq8eX2kY8_yxFnCLajzrEE3p7EtY"
GEMINI_API_KEY = "AIzaSyBzg_66XVCdCX2JYRObFNVOZYAkpHcNptM"

# ←←← BU YERGA QOLGAN 2 TA KALITNI QO‘SH
GOOGLE_API_KEY = "AIzaSyA_Cvc-r0jDfeQCnOWJO1x9ffHKUFZ1k30"   # Custom Search uchun
GOOGLE_CX = "3399766467a1d4c32"                              # Search Engine ID

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ===================== GEMINI CLIENT =====================
client = genai.Client(api_key=GEMINI_API_KEY)

def generate_text(prompt: str) -> str | None:
    model_names = [
        "gemini-2.5-flash",      # Eng tavsiya etiladi (tez va yaxshi)
        "gemini-2.5-pro",        # Kuchliroq variant
        "gemini-2.5-flash-lite"
    ]
    
    for model_name in model_names:
        try:
            logging.info(f"Model sinab ko‘rilmoqda: {model_name}")
            
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            
            if response and hasattr(response, 'text') and response.text:
                return response.text
                
        except Exception as e:
            logging.error(f"{model_name} da xato: {e}")
            continue
    
    return None


user_data = {}

# ===================== QOLGAN FUNKSIYALAR (get_image da GOOGLE_API_KEY ishlatiladi) =====================
def set_slide_background(slide, color_rgb):
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = color_rgb

def get_image(query):
    try:
        url = f"https://www.googleapis.com/customsearch/v1?q={query}&searchType=image&key={GOOGLE_API_KEY}&cx={GOOGLE_CX}&num=1"
        res = requests.get(url, timeout=5).json()
        if 'items' in res and res['items']:
            return res['items'][0]['link']
        return None
    except Exception as e:
        logging.error(f"Rasm qidirishda xato: {e}")
        return None

def create_pptx(raw_text, bg_type):
    # ... (oldingi create_pptx funksiyasi o‘zgarmagan, shu joyga qo‘y)
    prs = Presentation()
    sections = re.split(r'###', raw_text)
    bg_colors = {"blue": RGBColor(0, 32, 96), "dark": RGBColor(33, 33, 33), "white": RGBColor(255, 255, 255)}
    text_colors = {"blue": RGBColor(255, 255, 255), "dark": RGBColor(255, 255, 255), "white": RGBColor(0, 0, 0)}
   
    sel_bg = bg_colors.get(bg_type, bg_colors["white"])
    sel_txt = text_colors.get(bg_type, text_colors["white"])
   
    for section in sections:
        section = section.strip()
        if len(section) < 10: 
            continue
            
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        set_slide_background(slide, sel_bg)
       
        lines = section.split('\n')
        if not lines: continue
        title = slide.shapes.title
        title.text = lines[0].replace("*", "").strip()
        title.text_frame.paragraphs[0].font.color.rgb = sel_txt
       
        body = slide.placeholders[1]
        for line in lines[1:]:
            clean = line.strip().replace("*", "").replace("- ", "")
            if clean:
                p = body.text_frame.add_paragraph()
                p.text = clean
                p.font.size = Pt(18)
                p.font.color.rgb = sel_txt
       
        img_url = get_image(title.text)
        if img_url:
            try:
                img_data = requests.get(img_url, timeout=5).content
                slide.shapes.add_picture(io.BytesIO(img_data), Inches(5.5), Inches(1.5), width=Inches(4))
            except:
                pass
   
    buf = io.BytesIO()
    prs.save(buf)
    buf.seek(0)
    return buf


# ===================== HANDLERLAR (oldingi kabi) =====================
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Taqdimot mavzusini yozing!")

@dp.message(F.text)
async def start_flow(message: types.Message):
    if message.text.startswith('/'): 
        return
    user_data[message.from_user.id] = message.text
    kb = InlineKeyboardBuilder()
    kb.row(
        types.InlineKeyboardButton(text="🔵 Ko'k", callback_data="bg_blue"),
        types.InlineKeyboardButton(text="⚫️ Qora", callback_data="bg_dark"),
        types.InlineKeyboardButton(text="⚪️ Oq", callback_data="bg_white")
    )
    await message.answer("Fonni tanlang:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("bg_"))
async def handle_callback(callback: types.CallbackQuery):
    bg_type = callback.data.split("_")[1]
    topic = user_data.get(callback.from_user.id)
    
    if not topic:
        await callback.message.answer("Mavzu topilmadi. Qaytadan yozing.")
        return

    await callback.message.edit_text(f"⏳ '{topic}' tayyorlanmoqda...")

    try:
        prompt = f"Write 5 clear and educational slides about {topic} in Uzbek language. Separate each slide with ###"
        
        res_text = generate_text(prompt)
        
        if not res_text:
            raise Exception("Gemini javob bermadi. API kalitni yoki internetni tekshiring.")

        pptx_buffer = create_pptx(res_text, bg_type)
        file = types.BufferedInputFile(pptx_buffer.read(), filename=f"{topic[:50]}.pptx")
        
        await callback.message.answer_document(file, caption="✅ Taqdimot tayyor bo‘ldi!")
        await callback.message.delete()
        
    except Exception as e:
        logging.error(f"Umumiy xato: {e}")
        await callback.message.answer(f"❌ Xato: {str(e)[:400]}")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
