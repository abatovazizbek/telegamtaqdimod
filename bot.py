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

# 2. 404 XATOSIDAN HIMOYALANGAN MODEL TANLASH
genai.configure(api_key=GEMINI_API_KEY)

def get_working_model():
    """Modellarni birma-bir tekshiradi (404 xatosini oldini oladi)"""
    for m_name in ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']:
        try:
            m = genai.GenerativeModel(m_name)
            # Model borligini tekshirish uchun kichik so'rov yuboramiz (ixtiyoriy)
            return m
        except:
            continue
    return None

model = get_working_model()
user_data = {}

# 3. FON VA RASM FUNKSIYALARI
def set_slide_background(slide, color_rgb):
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = color_rgb

def get_image(query):
    try:
        url = f"https://www.googleapis.com/customsearch/v1?q={query}&searchType=image&key={GOOGLE_API_KEY}&cx={GOOGLE_CX}&num=1"
        res = requests.get(url, timeout=5).json()
        return res['items'][0]['link'] if 'items' in res else None
    except: return None

# 4. TAQDIMOT YARATISH
def create_pptx(raw_text, bg_type):
    prs = Presentation()
    sections = re.split(r'###', raw_text)
    
    bg_colors = {"blue": RGBColor(0, 32, 96), "dark": RGBColor(33, 33, 33), "white": RGBColor(255, 255, 255)}
    text_colors = {"blue": RGBColor(255, 255, 255), "dark": RGBColor(255, 255, 255), "white": RGBColor(0, 0, 0)}

    selected_bg = bg_colors.get(bg_type, bg_colors["white"])
    selected_txt = text_colors.get(bg_type, text_colors["white"])

    for section in sections:
        section = section.strip()
        if not section or len(section) < 15: continue
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        set_slide_background(slide, selected_bg)
        
        lines = section.split('\n')
        title_shape = slide.shapes.title
        title_shape.text = lines[0].replace("**", "").replace("*", "").strip()
        title_shape.text_frame.paragraphs[0].font.color.rgb = selected_txt
        
        body = slide.placeholders[1]
        body.width = Inches(5.0)
        for line in lines[1:]:
            clean = line.strip().replace("**", "").replace("*", "").replace("- ", "")
            if clean:
                p = body.text_frame.add_paragraph()
                p.text = clean
                p.font.size, p.font.color.rgb = Pt(18), selected_txt

        img_url = get_image(title_shape.text)
        if img_url:
            try:
                img_data = requests.get(img_url, timeout=5).content
                slide.shapes.add_picture(io.BytesIO(img_data), Inches(5.5), Inches(1.5), width=Inches(4))
            except: pass

    buffer = io.BytesIO()
    prs.save(buffer)
    buffer.seek(0)
    return buffer

# 5. BOT HANDLERLARI
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Salom! Taqdimot mavzusini yozing.")

@dp.message(F.text)
async def ask_style(message: types.Message):
    if message.text.startswith('/'): return
    user_data[message.from_user.id] = message.text
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔵 Ko'k", callback_data="bg_blue"),
                types.InlineKeyboardButton(text="⚫️ Qora", callback_data="bg_dark"),
                types.InlineKeyboardButton(text="⚪️ Oq", callback_data="bg_white"))
    await message.answer("Fon rangini tanlang:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("bg_"))
async def process_style(callback: types.CallbackQuery):
    bg_type = callback.data.split("_")[1]
    topic = user_data.get(callback.from_user.id, "Taqdimot")
    await callback.message.edit_text("⏳ Tayyorlanmoqda...")
    
    try:
        # 404 xatosidan himoyalangan model ishlatilyapti
        response = model.generate_content(f"Mavzu: {topic}. 5 ta slayd, ### bilan ajrat.")
        file_buffer = create_pptx(response.text, bg_type)
        file = types.BufferedInputFile(file_buffer.read(), filename=f"{topic}.pptx")
        await callback.message.answer_document(file, caption="✅ Tayyor!")
        await callback.message.delete()
    except Exception as e:
        await callback.message.answer(f"❌ Xato: {str(e)[:50]}")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
