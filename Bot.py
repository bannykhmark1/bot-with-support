from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, CallbackContext, ConversationHandler, MessageHandler, filters
import requests
import os
from dotenv import load_dotenv

# Константы для взаимодействия с Yandex + Telegram
TELEGRAM_BOT_TOKEN = ''
YANDEX_TRACKER_URL = 'https://api.tracker.yandex.net/v2/issues/'
YANDEX_TRACKER_ORG_ID = ''
YANDEX_TRACKER_OAUTH_TOKEN = ''
YANDEX_TRACKER_QUEUE = ''

# TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM")
# YANDEX_TRACKER_URL = os.getenv("YANDEX_URL")
# YANDEX_TRACKER_ORG_ID = os.getenv("YANDEX_ORG_ID")
# YANDEX_TRACKER_OAUTH_TOKEN = os.getenv("YANDEX_OAUTH_TOKEN")
# YANDEX_TRACKER_QUEUE = os.getenv("YANDEX_QUEUE")

# Состояния разговора
SUMMARY, DESCRIPTION = range(2)

def create_task(summary, description):
    headers = {
        'Authorization': f'OAuth {YANDEX_TRACKER_OAUTH_TOKEN}',
        'X-Cloud-Org-ID': YANDEX_TRACKER_ORG_ID,
        'Content-Type': 'application/json'
    }

    data = {
        'summary': summary,
        'description': description,
        'queue': YANDEX_TRACKER_QUEUE
    }

    print("Request Headers:", headers)
    print("Request Data:", data)

    response = requests.post(YANDEX_TRACKER_URL, json=data, headers=headers)
    
    print("Response Status Code:", response.status_code)
    print("Response Data:", response.json())

    return response

async def start(update: Update, context: CallbackContext) -> None:
    reply_keyboard = [['📝 Создать задачу', '❌ Отмена']]
    await update.message.reply_text(
        'Привет! Выберите команду для продолжения:',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )

async def new_task_start(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text('Пожалуйста, введите название задачи.', reply_markup=ReplyKeyboardRemove())
    return SUMMARY

async def summary_received(update: Update, context: CallbackContext) -> int:
    context.user_data['summary'] = update.message.text
    reply_keyboard = [['🔙 Назад', '❌ Отмена']]
    await update.message.reply_text('Теперь введите описание задачи.', reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True))
    return DESCRIPTION

async def description_received(update: Update, context: CallbackContext) -> int:
    summary = context.user_data['summary']
    description = update.message.text

    response = create_task(summary, description)
    task = response.json()

    print("Task Response:", task)
    if response.status_code == 201:
        task_id = task.get('id', 'Неизвестно')
        response_message = f"Задача создана: {task.get('key', 'Нет ключа')} - https://tracker.yandex.ru/{task_id}"
    else:
        response_message = f"Ошибка создания задачи: {task.get('errorMessages', ['Неизвестная ошибка'])[0]}"
    
    reply_keyboard = [['📝 Создать задачу', '❌ Отмена']]
    await update.message.reply_text(response_message, reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True))
    return ConversationHandler.END

async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text('Создание задачи отменено.', reply_markup=ReplyKeyboardMarkup([['📝 Создать задачу', '❌ Отмена']], one_time_keyboard=True, resize_keyboard=True))
    return ConversationHandler.END

async def back(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text('Пожалуйста, введите название задачи.', reply_markup=ReplyKeyboardRemove())
    return SUMMARY

def main() -> None:
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^📝 Создать задачу$'), new_task_start)],
        states={
            SUMMARY: [MessageHandler(filters.TEXT & ~filters.COMMAND, summary_received)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, description_received),
                          MessageHandler(filters.Regex('^🔙 Назад$'), back)]
        },
        fallbacks=[MessageHandler(filters.Regex('^❌ Отмена$'), cancel)]
    )
    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)

    application.run_polling()

if __name__ == '__main__':
    main()