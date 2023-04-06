import os

from discord import MessageType
from dotenv import load_dotenv

import constants
import gpt
from util import initiate_thread, update_thread_model, match_model_by_emoji, collect_and_send

import openai
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
DEFAULT_MODEL = gpt.GPTModel.CHAT_GPT


@bot.event
async def on_ready() -> None:
    """
    Called when the bot has successfully connected to Discord.
    """
    print(f'{bot.user.name} has connected to Discord!')


@bot.command(name='start', help='Starts a new conversation session.')
async def start(ctx: commands.Context) -> None:
    """
    Starts a new conversation session by sending a welcome message to the user.
    """
    await ctx.send(constants.WELCOME_MESSAGE)


@bot.listen('on_raw_reaction_add')
async def on_reaction(payload: discord.RawReactionActionEvent):
    """
    This function is called every time a reaction event is fired in any channel the bot is a member of.
    The reaction is used to determine a GPT version to use within a given thread.

    Args:
        payload: incoming payload containing emoji reaction and message ID.
    """
    # Ignore bot reactions
    if payload.member.bot:
        return
    # if reaction is one of GPTModel emojis, update model
    model = match_model_by_emoji(payload.emoji.name)
    if model:
        channel = await bot.fetch_channel(payload.channel_id)
        thread = channel.get_thread(payload.message_id)
        await update_thread_model(thread, model)


@bot.listen('on_message')
async def on_message(message: discord.Message):
    """
    This function is called every time a message is sent in any channel the bot is a member of.

    The message content is used to construct a payload for the OpenAI GPT API.
    The response from the API is then sent back to the original thread using the `safe_send()` function.

    Args:
        message: The message object representing the message that triggered this function.
    """
    # Ignore bot or thread starter messages
    if message.author.bot or message.type is MessageType.thread_starter_message:
        return
    # The first message in the channel is the system message, ack with creating a thread
    if isinstance(message.channel, discord.TextChannel):
        await initiate_thread(message, DEFAULT_MODEL)
        return
    # Process commands
    if message.content.startswith(('!', '?')):
        await bot.process_commands(message)
        return
    async with message.channel.typing():
        messages, model = await construct_gpt_payload(message.channel)
        response = await openai.ChatCompletion.acreate(
            model=model.version,
            messages=messages
        )
        assistant_response = response['choices'][0]['message']['content']
    await safe_send(message.channel, assistant_response)


if __name__ == '__main__':
    bot.run(DISCORD_TOKEN)
