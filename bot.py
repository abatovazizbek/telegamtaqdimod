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
GOOGLE_API_KEY = "AIzaSyA_Cvc-r0jDfeQCnOWJO1x9ffHKUFZ1k30"
GOOGLE_CX = "3399766467a1d4c32"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Gemini sozlamalari
genai.configure(api_key=GEMINI_KEY)

# 2. MODELNI CHAQIRISH (404-GA QARSHI ENG KUCHLI USUL)
def get_ai_response(prompt):
    # Modellarning to'liq va aniq manzillari
    check_models = [
        'models/gemini-1.5-flash',
        'models/gemini-1.5-pro',
        'models/gemini-pro'
    ]
    
    for m_path in check_models:
        try:
            logging.info(f"Ulanishga urinish: {m_path}")
            # Bu yerda modelni v1 (stabil) versiyada chaqiramiz
            model = genai.GenerativeModel(model_name=m_path)
            response = model.generate_content(prompt)
            if response and response.text:
                return response.text
        except Exception as e:
            logging.error(f"{m_path} xatosi: {str(e)[:50]}")
            continue
    return None

user_data = {}

# 3. RASM QIDIRISH
def get_img(query):
    try:
        url = f"https://www.googleapis.com/customsearch/v1?q={query}&searchType=image&key={GOOGLE_API_KEY}&cx={GOOGLE_CX}&num=1"
        res = requests.get(url, timeout=5).json()
        return res['items'][0]['link'] if 'items' in res else None
    except: return None

# 4. TAQDIMOT YASASH
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
        title.text = lines[0].replace("*", "").strip()
        title.text_frame.paragraphs[0].font.color.rgb = s_tx
        
        body = slide.placeholders[1]
        for line in lines[1:]:
            clean = line.strip().replace("*", "").replace("- ", "")
            if clean:
                p = body.text_frame.add_paragraph()
                p.text = clean
                p.font.size, p.font.color.rgb = Pt(18), s_tx
        
        link = get_img(title.text)
        if link:
            try:
                img = requests.get(link, timeout=5).content
                slide.shapes.add_picture(io.BytesIO(img), Inches(5.5), Inches(1.5), width=Inches(4))
            except: pass
            
    buf = io.BytesIO()
    prs.save(buf)
    buf.seek(0)
    return buf

# 5. HANDLERLAR
@dp.message(Command("start"))
async def start(m: types.Message):
    await m.answer("Taqdimot mavzusini yozing!")

@dp.message(F.text)
async def ask_bg(m: types.Message):
    if m.text.startswith('/'): return
    user_data[m.from_user.id] = m.text
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="Ko'k", callback_data="bg_blue"),
           types.InlineKeyboardButton(text="Qora", callback_data="bg_dark"),
           types.InlineKeyboardButton(text="Oq", callback_data="bg_white"))
    await m.answer("Fonni tanlang:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("bg_"))
async def process(cb: types.CallbackQuery):
    bg = cb.data.split("_")[1]
    topic = user_data.get(cb.from_user.id)
    await cb.message.edit_text(f"⏳ '{topic}' tayyorlanmoqda...")
    
    try:
        content = get_ai_response(f"Write 5 slides about {topic} in Uzbek, separate with ###")
        if not content: raise Exception("AI bilan bog'lanib bo'lmadi (404 yoki Limit)")
        
        ppt = create_ppt(content, bg)
        f = types.BufferedInputFile(ppt.read(), filename=f"{topic}.pptx")
        await cb.message.answer_document(f, caption="Tayyor!")
        await cb.message.delete()
    except Exception as e:
        await cb.message.answer(f"❌ Xato: {str(e)}")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
