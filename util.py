import asyncio

from telegram.constants import ChatAction
from telegram.ext import CallbackContext


async def typing_action(context: CallbackContext, chat_id: int):
    """
    Coroutine that sends a "typing..." action to the chat every 5 seconds.

    Args:
        context (CallbackContext): The context object from Telegram.
        chat_id (int): The ID of the chat to send the action to.
    """
    while True:
        try:
            await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
            await asyncio.sleep(5.0)
        except asyncio.CancelledError:
            break
