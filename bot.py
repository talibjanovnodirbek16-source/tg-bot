import telebot
import os
import tempfile
from groq import Groq

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

def ask_ai(text):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text}
        ]
    )
    return response.choices[0].message.content

@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(message, "Салам! Я AI-помощник. Задай вопрос или отправь документ (PDF, Excel, Word).")

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    try:
        reply = ask_ai(message.text)
        bot.reply_to(message, reply)
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {e}")

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

        elif file_name.endswith(".csv"):
            text = downloaded.decode("utf-8", errors="ignore")

        elif file_name.endswith(".txt"):
            text = downloaded.decode("utf-8", errors="ignore")

        else:
            bot.reply_to(message, "Формат не поддерживается. Отправь PDF, Excel, Word, CSV или TXT.")
            return

        if not text.strip():
            bot.reply_to(message, "Не удалось извлечь текст из документа.")
            return

        prompt = f"Проанализируй этот документ:\n\n{text[:4000]}"
        reply = ask_ai(prompt)
        bot.reply_to(message, reply)

    except Exception as e:
        bot.reply_to(message, f"Ошибка при чтении документа: {e}")

bot.polling()
