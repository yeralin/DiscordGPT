import os

from dotenv import load_dotenv;

import constants
from util import construct_gpt_payload, safe_send

import openai
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
openai.api_key = os.getenv('OPENAI_API_KEY')


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


@bot.listen("on_message")
async def on_message(message: discord.Message):
    """
    This function is called every time a message is sent in any channel the bot is a member of.

    The message content is used to construct a payload for the OpenAI GPT API.
    The response from the API is then sent back to the original channel using the `safe_send()` function.

    :param message: The message object representing the message that triggered this function.
    """
    # Ignore bot messages
    if message.author.bot:
        return
    # The first message in the channel is the system message, ack.
    if isinstance(message.channel, discord.TextChannel):
        await message.add_reaction('👍')
        return
    # Process commands
    if message.content.startswith(('!', '?')):
        await bot.process_commands(message)
        return
    messages, model = await construct_gpt_payload(message.channel)
    response = await openai.ChatCompletion.acreate(
        model=model,
        messages=messages
    )
    assistant_response = response['choices'][0]['message']['content']
    await safe_send(message.channel, assistant_response)


if __name__ == '__main__':
    bot.run(TOKEN)
