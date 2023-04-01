import re
from typing import Dict, List, Tuple

import discord
import tiktoken

from constants import GPTModel, MODEL_MESSAGE_REGEX


async def safe_send(ctx: discord.abc.Messageable, text: str) -> None:
    """
    Sends a message to the given channel or user, breaking it up if necessary to avoid Discord's message length limit.
    """
    while len(text) > 2000:
        break_pos = text.rfind('\n', 0, 2000)
        await ctx.send(text[:break_pos])
        text = text[break_pos:]
    await ctx.send(text)

def calculate_tokens(msg: Dict[str, str], model: str = 'gpt-3.5-turbo') -> int:
    """
    Calculates the number of tokens required to process a message.

    Args:
    - msg: A dictionary containing the message to process.
    - model: A string representing the OpenAI model to use.

    Returns:
    An integer representing the number of tokens required to process the message.
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding('cl100k_base')
    if model == 'gpt-3.5-turbo':
        num_tokens = 4
        for key, value in msg.items():
            num_tokens += len(encoding.encode(value))
            if key == 'name':
                num_tokens += -1
        num_tokens += 2
        return num_tokens
    else:
        raise NotImplementedError(
            f'calculate_tokens() is not presently implemented for model {model}')

async def construct_gpt_payload(channel: discord.ChannelType) -> Tuple[List[Dict[str, str]], GPTModel]:
    """
    Constructs OpenAI GPT API message payload from the given channel.

    Args:
    - channel: A discord.ChannelType representing the channel to fetch messages from.

    Returns:
    A list of messages in the GPT API format.
    """
    model, limit = GPTModel.CHAT_GPT.value
    messages = []
    tokens = 0
    # Fetch system message (the first message in the thread)
    initial_message = [m async for m in channel.history(limit=1, oldest_first=True)][0]
    # Extract chosen GPT model from the initial message
    system_message = {'role': 'system', 'content': initial_message.system_content}
    tokens += calculate_tokens(system_message)
    messages.append(system_message)
    # Fetches history in reverse order
    async for msg in channel.history():
        entry = {
            'role': 'assistant' if msg.author.bot else 'user', 'content': msg.content
        }
        tokens += calculate_tokens(entry)
        if tokens > limit or msg == initial_message:
            break
        messages.insert(1, entry)
    return messages, model
