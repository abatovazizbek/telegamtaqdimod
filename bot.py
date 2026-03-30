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

# ==========================================
# 1. SOZLAMALAR (TOKEN VA KEYLAR)
# ==========================================
TOKEN = "8128500951:AAFsgE6uq8eX2kY8_yxFnCLajzrEE3p7EtY" #
GEMINI_KEY = "AIzaSyBzg_66XVCdCX2JYRObFNVOZYAkpHcNptM" #
# Unsplash uchun tekin API key (Rasm qidirish uchun)
UNSPLASH_KEY = "Client-ID hP_uWq8F8g1-YgP2sLh4u9C9H8_oWw_OqWw_OqWw_" #

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()
genai.configure(api_key=GEMINI_KEY)

# ==========================================
# 2. MODELNI AVTOMATIK TANLASH (404 xatosiga qarshi)
# ==========================================
def get_ai_content(prompt):
    # Loglardagi 404 xatosini chetlab o'tish uchun barcha variantlar
    model_variants = [
        'models/gemini-1.5-flash', 
        'models/gemini-1.5-pro', 
        'models/gemini-pro'
    ]
    
    for model_name in model_variants:
        try:
            logging.info(f"Urinish: {model_name}")
            model = genai.GenerativeModel(model_name=model_name)
            response = model.generate_content(prompt)
            if response and response.text:
                return response.text
        except Exception as e:
            logging.error(f"{model_name} ishlamadi: {e}")
            continue 
    return None

# ==========================================
# 3. RASM QIDIRISH (UNSPLASH)
# ==========================================
def get_image(query):
    try:
        url = f"https://api.unsplash.com/photos/random?query={query}&orientation=landscape"
        headers = {"Authorization": UNSPLASH_KEY}
        res = requests.get(url, headers=headers, timeout=5).json()
        return res['urls']['regular']
    except:
        return None

# ==========================================
# 4. TAQDIMOT YARATISH LOGIKASI
# ==========================================
def create_ppt(text, bg_type):
    prs = Presentation()
    sections = re.split(r'###', text)
    bg_cols = {"blue": RGBColor(0, 32, 96), "dark": RGBColor(33, 33, 33), "white": RGBColor(255, 255, 255)}
    tx_cols = {"blue": RGBColor(255, 255, 255), "dark": RGBColor(255, 255, 255), "white": RGBColor(0, 0, 0)}
    s_bg, s_tx = bg_cols.get(bg_type, bg_cols["white"]), tx_cols.get(bg_type, tx_cols["white"])

    for sec in sections:
        sec = sec.strip()
        if len(sec) < 10: continue
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        slide.background.fill.solid()
        slide.background.fill.fore_color.rgb = s_bg
        
        lines = sec.split('\n')
        title = slide.shapes.title
        title_text = lines[0].replace("*", "").strip()
        title.text = title_text
        title.text_frame.paragraphs[0].font.color.rgb = s_tx
        
        body = slide.placeholders[1]
        for line in lines[1:]:
            clean = line.strip().replace("*", "").replace("- ", "")
            if clean:
                p = body.text_frame.add_paragraph()
                p.text = clean
                p.font.size, p.font.color.rgb = Pt(18), s_tx
        
        img_url = get_image(title_text)
        if img_url:
            try:
                img_data = requests.get(img_url, timeout=5).content
                slide.shapes.add_picture(io.BytesIO(img_data), Inches(5.5), Inches(1.5), width=Inches(4))
            except: pass
                
    buf = io.BytesIO()
    prs.save(buf)
    buf.seek(0)
    return buf

# ==========================================
# 5. BOT HANDLERLARI
# ==========================================
user_data = {}

@dp.message(Command("start"))
async def start(m: types.Message):
    await m.answer("Salom! Taqdimot mavzusini yozing:")

@dp.message(F.text)
async def ask_bg(m: types.Message):
    if m.text.startswith('/'): return
    user_data[m.from_user.id] = m.text
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="🔵 Ko'k", callback_data="bg_blue"),
           types.InlineKeyboardButton(text="⚫️ Qora", callback_data="bg_dark"),
           types.InlineKeyboardButton(text="⚪️ Oq", callback_data="bg_white"))
    await m.answer("Fonni tanlang:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("bg_"))
async def process(cb: types.CallbackQuery):
    bg = cb.data.split("_")[1]
    topic = user_data.get(cb.from_user.id)
    await cb.message.edit_text(f"⏳ '{topic}' tayyorlanmoqda...")
    
    try:
        content = get_ai_content(f"Write 5 slides about {topic} in Uzbek, separate with ###")
        if not content: raise Exception("AI modellari javob bermadi.")
        
        ppt = create_ppt(content, bg)
        f = types.BufferedInputFile(ppt.read(), filename=f"{topic}.pptx")
        await cb.message.answer_document(f, caption=f"✅ {topic} tayyor!")
        await cb.message.delete()
    except Exception as e:
        await cb.message.answer(f"❌ Xato: {str(e)}")

async def main():
    # Conflictni oldini olish uchun webhookni tozalash
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
