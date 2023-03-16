from dotenv import load_dotenv; load_dotenv()  # Load all variables first
import logging
import os
import openai
import constants
from util import typing_action
from telegram import Update
from telegram.ext import (
    filters,
    ApplicationBuilder,
    CallbackContext,
    CommandHandler,
    MessageHandler,
    PicklePersistence,
)

from token_limiter.token_limiter import TokenizedMessageLimiter, Role

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


async def start(update: Update, context: CallbackContext) -> None:
    """
    Handles the /start command and initializes the message limiter.

    Args:
        update (Update): The update object from Telegram.
        context (CallbackContext): The context object from Telegram.
    """
    if 'tokenized_message_limiter' not in context.user_data:
        context.user_data[
            'tokenized_message_limiter'] = TokenizedMessageLimiter()

    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=constants.WELCOME_MESSAGE)


async def system(update: Update, context: CallbackContext) -> None:
    """
    Handles the /system command and sets the system message or gets the current one.

    Args:
        update (Update): The update object from Telegram.
        context (CallbackContext): The context object from Telegram.
    """
    if 'tokenized_message_limiter' not in context.user_data:
        context.user_data[
            'tokenized_message_limiter'] = TokenizedMessageLimiter()
    system_message = update.message.text.replace('/system', '').strip()
    tokenized_message_limiter = context.user_data['tokenized_message_limiter']
    if system_message:
        tokenized_message_limiter.set_system_message(system_message)
    else:
        system_message = tokenized_message_limiter.system_message.msg['content']
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f'Your current system message: {system_message}')


async def message(update: Update, context: CallbackContext) -> None:
    """
    Handles incoming messages from users and sends a response from the assistant.

    Args:
        update (Update): The update object from Telegram.
        context (CallbackContext): The context object from Telegram.
    """
    typing_task = context.application.create_task(
        typing_action(context, update.effective_chat.id))
    if 'tokenized_message_limiter' not in context.user_data:
        context.user_data[
            'tokenized_message_limiter'] = TokenizedMessageLimiter()
    user_text = update.message.text
    tokenized_message_limiter = context.user_data['tokenized_message_limiter']
    tokenized_message_limiter.add_message(user_text, Role.USER)
    response = await openai.ChatCompletion.acreate(
        model="gpt-3.5-turbo",
        messages=tokenized_message_limiter.serialize_messages()
    )
    assistant_response = response['choices'][0]['message']['content']
    tokenized_message_limiter.add_message(assistant_response,
                                          Role.ASSISTANT)
    typing_task.cancel()
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=assistant_response)


async def rejection(update: Update, context: CallbackContext) -> None:
    """
    Handles rejection messages for non-allowed users.

    Args:
        update (Update): The update object from Telegram.
        context (CallbackContext): The context object from Telegram.
    """
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=constants.REJECTION_MESSAGE)


def main() -> None:
    """
    Main entry for the Telegram bot.
    """
    # Configure optional user filter
    user_id = os.getenv("USER_ID")
    user_filter = filters.User(int(user_id)) if user_id else filters.ALL
    # Configure bot application
    persistence = PicklePersistence(filepath='./local_storage')
    application = ApplicationBuilder().token(
        os.getenv("TELEGRAM_TOKEN")).persistence(persistence).build()
    # Configure main handlers
    start_handler = CommandHandler('start', start, user_filter)
    system_handler = CommandHandler('system', system, user_filter)
    message_handler = MessageHandler(
        user_filter & filters.TEXT & (~filters.COMMAND), message)
    rejection_handler = MessageHandler(~user_filter, rejection)
    application.add_handlers(
        [start_handler, system_handler, message_handler, rejection_handler])
    application.run_polling()


if __name__ == '__main__':
    main()
