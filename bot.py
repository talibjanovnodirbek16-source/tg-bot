import telebot
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

@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(message, "Салам! Я AI-помощник. Задай любой вопрос.")

@bot.message_handler(func=lambda m: True)
def handle(message):
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message.text}
            ]
        )
        bot.reply_to(message, response.choices[0].message.content)
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {e}")

bot.polling()
