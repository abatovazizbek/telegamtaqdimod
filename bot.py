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

# 1. KONFIGURATSIYA
TOKEN = "8128500951:AAFsgE6uq8eX2kY8_yxFnCLajzrEE3p7EtY"
GEMINI_KEY = "AIzaSyBzg_66XVCdCX2JYRObFNVOZYAkpHcNptM"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()
genai.configure(api_key=GEMINI_KEY)

# 2. DUCKDUCKGO ORQALI RASM QIDIRISH (API KEY KERAK EMAS)
def get_duckduckgo_image(query):
    try:
        # DuckDuckGo dan rasm qidirish uchun vaqtinchalik yechim
        url = f"https://duckduckgo.com/assets/logo_homepage.normal.v108.svg" # Zaxira rasm
        search_url = "https://duckduckgo.com/i.js"
        params = {'q': query, 'o': 'json'}
        res = requests.get(search_url, params=params, timeout=5).json()
        if 'results' in res and len(res['results']) > 0:
            return res['results'][0]['image']
    except:
        pass
    return None

# 3. GEMINI MODELI (404 DAN HIMOYALANGAN)
def get_ai_content(prompt):
    # Eng chidamli modellar ro'yxati
    for m_path in ['models/gemini-1.5-flash', 'models/gemini-pro', 'gemini-1.5-flash']:
        try:
            model = genai.GenerativeModel(model_name=m_path)
            response = model.generate_content(prompt)
            if response and response.text:
                return response.text
        except:
            continue
    return None

user_data = {}

# 4. TAQDIMOT YARATISH
def create_ppt(text, bg_type):
    prs = Presentation()
    sections = re.split(r'###', text)
    bg_cols = {"blue": RGBColor(0, 32, 96), "dark": RGBColor(33, 33, 33), "white": RGBColor(255, 255, 255)}
    tx_cols = {"blue": RGBColor(255, 255, 255), "dark": RGBColor(255, 255, 255), "white": RGBColor(0, 0, 0)}
    
    s_bg = bg_cols.get(bg_type, bg_cols["white"])
    s_tx = tx_cols.get(bg_type, tx_cols["white"])

    for sec in sections:
        sec = sec.strip()
        if len(sec) < 10: continue
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        slide.background.fill.solid()
        slide.background.fill.fore_color.rgb = s_bg
        
        lines = sec.split('\n')
        title = slide.shapes.title
        title.text = lines[0].replace("*", "").strip()
        title.text_frame.paragraphs[0].font.color.rgb = s_tx
        
        body = slide.placeholders[1]
        for line in lines[1:]:
            clean = line.strip().replace("*", "").replace("- ", "")
            if clean:
                p = body.text_frame.add_paragraph()
                p.text = clean
                p.font.size, p.font.color.rgb = Pt(18), s_tx
        
        # DuckDuckGo dan rasm olish
        img_url = get_duckduckgo_image(title.text)
        if img_url:
            try:
                img_data = requests.get(img_url, timeout=5).content
                slide.shapes.add_picture(io.BytesIO(img_data), Inches(5.5), Inches(1.5), width=Inches(4))
            except: pass
            
    buf = io.BytesIO()
    prs.save(buf)
    buf.seek(0)
    return buf

# 5. BOT LOGIKASI
@dp.message(Command("start"))
async def start(m: types.Message):
    await m.answer("Assalomu alaykum! Taqdimot mavzusini kiriting:")

@dp.message(F.text)
async def choose_bg(m: types.Message):
    if m.text.startswith('/'): return
    user_data[m.from_user.id] = m.text
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="🔵 Ko'k", callback_data="bg_blue"),
           types.InlineKeyboardButton(text="⚫️ Qora", callback_data="bg_dark"),
           types.InlineKeyboardButton(text="⚪️ Oq", callback_data="bg_white"))
    await m.answer("Taqdimot uchun fon rangini tanlang:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("bg_"))
async def make_ppt(cb: types.CallbackQuery):
    bg = cb.data.split("_")[1]
    topic = user_data.get(cb.from_user.id)
    await cb.message.edit_text(f"⏳ '{topic}' mavzusida taqdimot tayyorlanmoqda...")
    
    try:
        content = get_ai_content(f"Write 5 slides about {topic} in Uzbek, separate with ###")
        if not content: raise Exception("AI hozir band. Keyinroq urinib ko'ring.")
        
        ppt_file = create_ppt(content, bg)
        doc = types.BufferedInputFile(ppt_file.read(), filename=f"{topic}.pptx")
        await cb.message.answer_document(doc, caption="✅ Taqdimotingiz tayyor!")
        await cb.message.delete()
    except Exception as e:
        await cb.message.answer(f"❌ Xatolik: {str(e)}")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
