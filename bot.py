import logging
import os
import openai
from dotenv import load_dotenv
from telegram import Update, Message
from telegram.ext import (
    filters,
    ApplicationBuilder,
    CallbackContext,
    CommandHandler,
    MessageHandler,
    PicklePersistence,
)
from token_limiter import MessageRole, TokenizedMessageLimiter

load_dotenv()
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

welcome_message = """I am TelegramGPT bot!

/system <system-message>
The system message helps set the behavior of the assistant 
For example, `/system You are a helpful assistant who answers questions clearly and concisely`

To learn more visit https://platform.openai.com/docs/guides/chat
"""

async def start(update: Update, context: CallbackContext) -> None:
    """
    Handles the /start command and initializes the message limiter.

    Args:
        update (Update): The update object from Telegram.
        context (CallbackContext): The context object from Telegram.

    Returns:
        None.
    """
    if 'tokenized_message_limiter' not in context.user_data:
        context.user_data['tokenized_message_limiter'] = TokenizedMessageLimiter()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=welcome_message)


async def system(update: Update, context: CallbackContext) -> None:
    """
    Handles the /system command and sets the system message or gets the current one.

    Args:
        update (Update): The update object from Telegram.
        context (CallbackContext): The context object from Telegram.

    Returns:
        None.
    """
    if 'tokenized_message_limiter' not in context.user_data:
        context.user_data['tokenized_message_limiter'] = TokenizedMessageLimiter()
    system_message = update.message.text.replace('/system', '').strip()
    tokenized_message_limiter = context.user_data['tokenized_message_limiter']
    if system_message:
        tokenized_message_limiter.set_system_message(system_message)
    else:
        system_message = tokenized_message_limiter.system_message.msg['content']
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f'Your current system message: {system_message}')


async def message(update: Update, context: CallbackContext) -> None:
    """
    Handles incoming messages from users and sends a response from the assistant.

    Args:
        update (Update): The update object from Telegram.
        context (CallbackContext): The context object from Telegram.

    Returns:
        None.
    """
    if 'tokenized_message_limiter' not in context.user_data:
        context.user_data['tokenized_message_limiter'] = TokenizedMessageLimiter()
    user_text = update.message.text
    tokenized_message_limiter = context.user_data['tokenized_message_limiter']
    tokenized_message_limiter.add_message(user_text, MessageRole.USER)
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=tokenized_message_limiter.serialize_messages()
    )
    assistant_response = response['choices'][0]['message']['content']
    tokenized_message_limiter.add_message(assistant_response, MessageRole.ASSISTANT)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=assistant_response)


def main() -> None:
    """
    Main entry for the Telegram bot.
    """
    openai.api_key = os.getenv("OPENAI_API_KEY")
    persistence = PicklePersistence(filepath='./local_storage')
    application = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")
                                             ).persistence(persistence).build()
    start_handler = CommandHandler('start', start)
    system_handler = CommandHandler('system', system)
    message_handler = MessageHandler(
        filters.TEXT & (~filters.COMMAND), message)
    application.add_handlers([start_handler, system_handler, message_handler])
    application.run_polling()


if __name__ == '__main__':
    main()
