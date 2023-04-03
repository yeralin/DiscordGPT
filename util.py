from typing import Union

import discord

from constants import GPTModel


async def safe_send(ctx: discord.abc.Messageable, text: str) -> None:
    """
    Sends a message to the given channel or user, breaking it up if necessary to avoid Discord's message length limit.
    """
    while len(text) > 2000:
        break_pos = text.rfind('\n', 0, 2000)
        await ctx.send(text[:break_pos])
        text = text[break_pos:]
    await ctx.send(text)


async def initiate_thread(message: discord.Message, model: GPTModel):
    """
    Create a thread with a given GPT version

    Args:
        message: thread's starter message
        model: thread's GPT model
    """
    thread = await message.create_thread(name=f'Using model: {model.version}')
    await thread.starter_message.add_reaction(model.emoji)


async def update_thread_model(thread: discord.Thread, model: GPTModel):
    """
    Update a thread to provided GPT version

    Args:
        thread: target thread
        model: thread's GPT model
    """
    starter_message = thread.starter_message
    if not starter_message:  # starter_message is not cached
        starter_message = await thread.parent.fetch_message(thread.id)
    await starter_message.clear_reactions()
    await starter_message.add_reaction(model.emoji)
    await thread.edit(name=f'Using model: {model.version}')


def match_model_by_emoji(emoji: str) -> Union[GPTModel, None]:
    """
    Returns a GPTModel enum value that matches the specified emoji.

    Args:
        emoji (str): The emoji string to match.

    Returns:
        GPTModel or None: The GPTModel enum value that matches the specified emoji,
            or None if no match is found.
    """
    for model in GPTModel:
        if emoji == model.emoji:
            return model
    return None
