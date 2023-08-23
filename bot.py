import os

from discord import MessageType
from dotenv import load_dotenv

import constants
from gpt import GPTModel
from discord_util import DiscordUtil

import openai
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')


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


@bot.listen('on_interaction')
async def on_interaction(interaction: discord.Interaction):
    """
    Processes interactions with the bot and triggers actions based on the interaction type.

    Args:
        interaction: An Interaction object that contains the data about the interaction.
    """
    if interaction.type == discord.InteractionType.component:
        custom_id = interaction.data['custom_id']

        # GPT Model selected
        if 'model' in custom_id:
            selected_value = custom_id.split('_')[-1]
            selected_model = GPTModel.from_version(selected_value)
            await interaction.channel.edit(name=f'Using model: {selected_model.version}')
            await interaction.response.edit_message(**DiscordUtil.generate_model_options(selected_model))

        # Temperature selected
        elif 'temperature' in custom_id:
            selected_value = interaction.data['values'][0]
            selected_temperature = float(selected_value)
            await interaction.response.edit_message(**DiscordUtil.generate_temperature_options(selected_temperature))

        # Top P Value selected
        elif 'top_p' in custom_id:
            selected_value = interaction.data['values'][0]
            selected_top_p = float(selected_value)
            await interaction.response.edit_message(**DiscordUtil.generate_top_p_value_options(selected_top_p))


@bot.listen('on_raw_reaction_add')
async def on_reaction(payload: discord.RawReactionActionEvent):
    """
    This function is called every time a reaction event is fired in any channel the bot is a member of.

    Args:
        payload: incoming payload containing emoji reaction and message ID.
    """
    # Ignore bot reactions
    if payload.member.bot:
        return
    # Regenerate the response
    if payload.emoji.name == '🔁':
        channel = await bot.fetch_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        await message.delete()
        await DiscordUtil.collect_and_send(channel)


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
        await DiscordUtil.initiate_thread(message)
        return
    # Process commands
    if message.content.startswith(('!', '?')):
        await bot.process_commands(message)
        return
    await DiscordUtil.collect_and_send(message.channel)


if __name__ == '__main__':
    bot.run(DISCORD_TOKEN)
