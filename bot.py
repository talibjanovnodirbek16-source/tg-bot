import telebot
import requests
import os
import tempfile
from groq import Groq
from urllib.parse import quote

TELEGRAM_TOKEN = "8646600794:AAFVUJUIZS5Mq8AHnoBibTMxx0iPRBbuksk"
GROQ_API_KEY = "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"

client = Groq(api_key=GROQ_API_KEY)
bot = telebot.TeleBot(TELEGRAM_TOKEN)

SYSTEM_PROMPT = """Ты умный AI-помощник.

При каждом ответе:
1. Отвечай на вопрос пользователя
2. Если в тексте есть элементы рибы (проценты, пени, штрафы за просрочку) — укажи:
   🚨 ВНИМАНИЕ: РИБА
   - Что именно является рибой
   - Почему это запрещено в исламе
   - Халяльная альтернатива

Отвечай на русском языке."""

IMAGE_KEYWORDS = ["нарисуй", "сгенерируй картинку", "создай изображение", "нарисовать", "сгенерировать изображение", "draw", "generate image", "create image", "нарисуй мне"]

def ask_ai(text):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text}
        ]
    )
    return response.choices[0].message.content

def generate_image(chat_id, prompt):
    try:
        encoded = quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true"
        response = requests.get(url, timeout=60)
        if response.status_code == 200:
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
                f.write(response.content)
                tmp_path = f.name
            with open(tmp_path, "rb") as photo:
                bot.send_photo(chat_id, photo, caption=f"🎨 {prompt}")
            os.unlink(tmp_path)
        else:
            bot.send_message(chat_id, "Не удалось сгенерировать. Попробуй ещё раз.")
    except Exception as e:
        bot.send_message(chat_id, f"Ошибка: {e}")

@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(message, "Салам! Я AI-помощник.\n\nМогу отвечать на вопросы, генерировать изображения и читать документы.\n\nПросто напиши что нужно!")

@bot.message_handler(commands=["image"])
def image_command(message):
    prompt = message.text.replace("/image", "").strip()
    if not prompt:
        bot.reply_to(message, "Напиши описание. Пример:\n/image закат над горами")
        return
    bot.reply_to(message, "Генерирую изображение...")
    generate_image(message.chat.id, prompt)

@bot.message_handler(content_types=["document"])
def handle_document(message):
    try:
        bot.reply_to(message, "Читаю документ...")
        file_info = bot.get_file(message.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        file_name = message.document.file_name.lower()
        text = ""

        if file_name.endswith(".pdf"):
            import pdfplumber
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                f.write(downloaded)
                tmp_path = f.name
            with pdfplumber.open(tmp_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""
            os.unlink(tmp_path)

        elif file_name.endswith(".xlsx") or file_name.endswith(".xls"):
            import openpyxl
            with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
                f.write(downloaded)
                tmp_path = f.name
            wb = openpyxl.load_workbook(tmp_path)
            for sheet in wb.sheetnames:
                ws = wb[sheet]
                for row in ws.iter_rows(values_only=True):
                    text += " | ".join([str(c) for c in row if c is not None]) + "\n"
            os.unlink(tmp_path)

        elif file_name.endswith(".docx"):
            import docx
            with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
                f.write(downloaded)
                tmp_path = f.name
            doc = docx.Document(tmp_path)
            for para in doc.paragraphs:
                text += para.text + "\n"
            os.unlink(tmp_path)

        elif file_name.endswith(".csv") or file_name.endswith(".txt"):
            text = downloaded.decode("utf-8", errors="ignore")

        else:
            bot.reply_to(message, "Формат не поддерживается.")
            return

        if not text.strip():
            bot.reply_to(message, "Не удалось извлечь текст.")
            return

        prompt = f"Проанализируй этот документ:\n\n{text[:4000]}"
        reply = ask_ai(prompt)
        bot.reply_to(message, reply)

    except Exception as e:
        bot.reply_to(message, f"Ошибка при чтении документа: {e}")

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    text = message.text.lower()
    if any(kw in text for kw in IMAGE_KEYWORDS):
        bot.reply_to(message, "Генерирую изображение...")
        generate_image(message.chat.id, message.text)
    else:
        try:
            reply = ask_ai(message.text)
            bot.reply_to(message, reply)
        except Exception as e:
            bot.reply_to(message, f"Ошибка: {e}")

bot.polling()
