import os
import asyncio
import logging
import io
import re
import requests
import google.generativeai as genai
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from pptx import Presentation
from pptx.util import Pt, Inches
from pptx.dml.color import RGBColor

# 1. SOZLAMALAR
TOKEN = "8128500951:AAFsgE6uq8eX2kY8_yxFnCLajzrEE3p7EtY"
GEMINI_API_KEY = "AIzaSyBzg_66XVCdCX2JYRObFNVOZYAkpHcNptM"
GOOGLE_API_KEY = "AIzaSyA_Cvc-r0jDfeQCnOWJO1x9ffHKUFZ1k30"
GOOGLE_CX = "3399766467a1d4c32"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# 2. GEMINI KONFIGURATSIYASI (v1 versiyaga majburlash)
genai.configure(api_key=GEMINI_API_KEY)

def generate_text(prompt):
    """
    404 xatosini oldini olish uchun eng ishonchli model nomlarini sinaydi
    """
    # Eng stabil model nomlari ro'yxati
    model_names = ['gemini-1.5-flash-latest', 'gemini-1.5-flash', 'gemini-pro']
    
    for name in model_names:
        try:
            logging.info(f"Modelga so'rov yuborilmoqda: {name}")
            model = genai.GenerativeModel(model_name=name)
            response = model.generate_content(prompt)
            if response and response.text:
                return response.text
        except Exception as e:
            logging.error(f"{name} xatosi: {e}")
            continue
    return None

user_data = {}

# 3. TAQDIMOT VA RASM FUNKSIYALARI
def set_slide_background(slide, color_rgb):
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = color_rgb

def get_image(query):
    try:
        url = f"https://www.googleapis.com/customsearch/v1?q={query}&searchType=image&key={GOOGLE_API_KEY}&cx={GOOGLE_CX}&num=1"
        res = requests.get(url, timeout=5).json()
        return res['items'][0]['link'] if 'items' in res else None
    except: return None

def create_pptx(raw_text, bg_type):
    prs = Presentation()
    sections = re.split(r'###', raw_text)
    bg_colors = {"blue": RGBColor(0, 32, 96), "dark": RGBColor(33, 33, 33), "white": RGBColor(255, 255, 255)}
    text_colors = {"blue": RGBColor(255, 255, 255), "dark": RGBColor(255, 255, 255), "white": RGBColor(0, 0, 0)}
    
    sel_bg = bg_colors.get(bg_type, bg_colors["white"])
    sel_txt = text_colors.get(bg_type, text_colors["white"])

    for section in sections:
        section = section.strip()
        if len(section) < 10: continue
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        set_slide_background(slide, sel_bg)
        
        lines = section.split('\n')
        title = slide.shapes.title
        title.text = lines[0].replace("*", "").strip()
        title.text_frame.paragraphs[0].font.color.rgb = sel_txt
        
        body = slide.placeholders[1]
        for line in lines[1:]:
            clean = line.strip().replace("*", "").replace("- ", "")
            if clean:
                p = body.text_frame.add_paragraph()
                p.text = clean
                p.font.size, p.font.color.rgb = Pt(18), sel_txt
        
        img_url = get_image(title.text)
        if img_url:
            try:
                img_data = requests.get(img_url, timeout=5).content
                slide.shapes.add_picture(io.BytesIO(img_data), Inches(5.5), Inches(1.5), width=Inches(4))
            except: pass
    
    buf = io.BytesIO()
    prs.save(buf)
    buf.seek(0)
    return buf

# 4. BOT HANDLERLARI
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Taqdimot mavzusini yozing!")

@dp.message(F.text)
async def start_flow(message: types.Message):
    if message.text.startswith('/'): return
    user_data[message.from_user.id] = message.text
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="🔵 Ko'k", callback_data="bg_blue"),
           types.InlineKeyboardButton(text="⚫️ Qora", callback_data="bg_dark"),
           types.InlineKeyboardButton(text="⚪️ Oq", callback_data="bg_white"))
    await message.answer("Fonni tanlang:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("bg_"))
async def handle_callback(callback: types.CallbackQuery):
    bg_type = callback.data.split("_")[1]
    topic = user_data.get(callback.from_user.id)
    await callback.message.edit_text(f"⏳ '{topic}' tayyorlanmoqda...")
    
    try:
        # Yangilangan ishonchli funksiya
        res_text = generate_text(f"Write 5 slides about {topic} in Uzbek, separate with ###")
        if not res_text:
            raise Exception("AI javob bermadi. API kalitni tekshiring.")

        pptx = create_pptx(res_text, bg_type)
        file = types.BufferedInputFile(pptx.read(), filename=f"{topic}.pptx")
        await callback.message.answer_document(file, caption="Tayyor!")
        await callback.message.delete()
    except Exception as e:
        await callback.message.answer(f"❌ Xato: {str(e)}")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
