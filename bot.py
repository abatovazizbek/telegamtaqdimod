import os
import asyncio
import logging
import io
import re
import google.generativeai as genai
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from pptx import Presentation
from pptx.util import Pt, Inches
from pptx.dml.color import RGBColor

# 1. SOZLAMALAR (Railway Variables'dan o'qiydi)
TOKEN = "8128500951:AAFsgE6uq8eX2kY8_yxFnCLajzrEE3p7EtY"
GEMINI_KEY = os.getenv("GEMINI_KEY")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Gemini sozlamasi - 400 API Key xatosini oldini olish uchun
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
    logging.info("✅ GEMINI_KEY Railway'dan muvaffaqiyatli o'qildi.")
else:
    logging.error("❌ XATO: GEMINI_KEY o'zgaruvchisi topilmadi!")

# 2. MODELNI CHAQIRISH (404 xatosini tuzatish)
def get_ai_content(topic):
    try:
        # 'models/' prefiksini ishlatmaymiz, bu 404 xatosini yo'qotadi
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"Write 5 slides about {topic} in Uzbek. Use ### to separate slides."
        response = model.generate_content(prompt)
        return response.text if response else None
    except Exception as e:
        logging.error(f"AI Xatosi: {str(e)}")
        return None

# 3. TAQDIMOT (.pptx) YARATISH
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
        for line in lines[1:5]:
            clean = line.strip().replace("*", "").replace("- ", "")
            if clean:
                p = body.text_frame.add_paragraph()
                p.text = clean[:120]
                p.font.size, p.font.color.rgb = Pt(18), s_tx
                
    buf = io.BytesIO()
    prs.save(buf)
    buf.seek(0)
    return buf

# 4. HANDLERLAR
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
    msg = await cb.message.edit_text(f"⏳ '{topic}' tayyorlanmoqda...")
    
    content = get_ai_content(topic)
    if content:
        ppt = create_ppt(content, bg)
        f = types.BufferedInputFile(ppt.read(), filename=f"{topic}.pptx")
        await cb.message.answer_document(f, caption=f"✅ '{topic}' tayyor!")
        await msg.delete()
    else:
        await cb.message.answer(f"❌ Xato: Gemini javob bermadi. API kalitni tekshiring.")

async def main():
    # TelegramConflictError ni oldini olish
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
