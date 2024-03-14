from typing import List, Dict

import discord
from constants import DEFAULT_MODEL, DEFAULT_TEMPERATURE, DEFAULT_TOP_P, LLMModel
from openai import RateLimitError

from llm.base_llm import LLM


class RetryButton(discord.ui.View):
    """
    This class is invoked when `openai.error.RateLimitError` is thrown in `collect_and_send` method.
    It is responsible for rendering retry button and handling the retry mechanism.
    """

    @discord.ui.button(label='Retry', style=discord.ButtonStyle.primary)
    async def retry_callback(self, interaction: discord.Interaction, _: discord.ui.Button):
        """
        This function handles user press on the retry button. It deletes the original retry message,
            and re-tries to send payload.
        Args:
            interaction: The interaction object which contains the context of the chat
            _: button object, ignored
        """
        await interaction.message.delete()
        await DiscordUtil.collect_and_send(interaction.channel)


class DiscordUtil:
    """
    This class is responsible for all interactions with the Discord API.
    """

    @staticmethod
    async def safe_send(ctx: discord.abc.Messageable, text: str, view: discord.ui.View = None) -> None:
        """
        Sends a message to the given channel or user, breaking it up if necessary to avoid Discord's message length limit.
        """
        while len(text) > 2000:
            break_pos = text.rfind('\n', 0, 2000)
            await ctx.send(text[:break_pos])
            text = text[break_pos:]
        await ctx.send(text, view=view if view else None)

    @staticmethod
    async def collect_and_send(thread: discord.Thread, llm_clients: Dict[str, LLM]) -> None:
        """
        Collects history messages from the thread, communicates with the LLM, and sends the response back.

        This function is responsible for collecting messages from the given thread, constructing a payload
        to send to the LLM, and sending the response back to the thread.

        Args:
            thread (discord.Thread): The thread where messages are collected and the assistant's response is sent.
            llm_clients (Dict[str, LLM]): A dictionary of LLM clients.

        Raises:
            openai.error.RateLimitError: If the rate limit is exceeded for the GPT API call.
                It renders a RetryButton for retrying the process.
        """
        async with (thread.typing()):
            try:
                starter_message, model_message, temperature_message, top_p_message = [m async for m in
                                                                                      thread.history(limit=4,
                                                                                                     oldest_first=True)]
                if not starter_message: # starter_message is not cached
                    starter_message = await thread.parent.fetch_message(starter_message.id)
                system_message = starter_message.system_content

                # Extract configurations
                temperature = float(DiscordUtil.extract_set_value(temperature_message))
                top_p = float(DiscordUtil.extract_set_value(top_p_message))
                model = LLMModel.from_version(DiscordUtil.extract_set_value(model_message))

                # Collect message history
                history = []
                async for msg in thread.history():
                    # Skip configuration messages and system messages
                    if msg in (starter_message, model_message, temperature_message, top_p_message) \
                            or msg.system_content != msg.content:
                        continue
                    history.insert(0, msg)

                # Communicate with LLM
                assistant_response = await llm_clients[model.vendor].communicate(history, model, temperature, top_p, system_message)
                await DiscordUtil.safe_send(thread, assistant_response)
            except RateLimitError as ex:
                # Render retry button on rate limit
                await DiscordUtil.safe_send(thread, ex.user_message, view=RetryButton())
            except Exception as ex:
                await DiscordUtil.safe_send(thread, str(ex))

    @staticmethod
    async def initiate_thread(message: discord.Message):
        """
        Initiates a thread in Discord.

        Parameters:
            message (discord.Message): The message object that triggered the function.
        """
        thread = await message.create_thread(name=f'Using model: {DEFAULT_MODEL.version}')
        await thread.send(**DiscordUtil.generate_model_options())
        await thread.send(**DiscordUtil.generate_temperature_options())
        await thread.send(**DiscordUtil.generate_top_p_value_options())

    @staticmethod
    def generate_model_options(selected_model: LLMModel = DEFAULT_MODEL):
        """
        Generates GPT model options as Select Menu.
        """
        view = discord.ui.View()

        for (i, model) in enumerate(LLMModel):
            row = i // 5
            if model == selected_model:
                button = discord.ui.Button(style=discord.ButtonStyle.success, row=row, label=model.version,
                                           custom_id=f'model_{model.version}', disabled=True)
            else:
                button = discord.ui.Button(style=discord.ButtonStyle.primary, row=row, label=model.version,
                                           custom_id=f'model_{model.version}', disabled=not model.available)
            view.add_item(button)
        return {
            'content': '**Model**:',
            'view': view
        }

    @staticmethod
    def generate_temperature_options(selected_temperature: float = DEFAULT_TEMPERATURE):
        """
        Generates temperature options as Select Menu.
        """
        view = discord.ui.View()
        select_menu = discord.ui.Select(custom_id='temperature_select', placeholder='Select Temperature')
        for temperature in [0, .25, .5, .75, 1, 1.25, 1.5, 1.75, 2]:
            select_menu.add_option(label=f'{temperature}', value=f'{temperature}',
                                   default=(temperature == selected_temperature))
        view.add_item(select_menu)
        return {
            'content': '**Temperature** (controls the randomness of the generated responses):',
            'view': view
        }

    @staticmethod
    def generate_top_p_value_options(selected_top_p: float = DEFAULT_TOP_P):
        """
        Generates top p value options as Select Menu.
        """
        view = discord.ui.View()
        select_menu = discord.ui.Select(custom_id='top_p_select', placeholder='Select Top P Value')
        for top_p in [.1, .2, .3, .4, .5, .6, .7, .8, .9, 1]:
            select_menu.add_option(label=f'{top_p}', value=f'{top_p}', default=(top_p == selected_top_p))
        view.add_item(select_menu)
        return {
            'content': '**Top P value** (controls the diversity and quality of the responses):',
            'view': view
        }

    @staticmethod
    def extract_set_value(select_message):
        content = select_message.content.lower()
        for component in select_message.components:
            for child in component.children:
                if 'model' in content:  # process model buttons
                    if child.style is discord.ButtonStyle.success:
                        return child.label
                else:  # process drop down menu selections
                    for option in child.options:
                        if option.default:
                            return option.label
        return None
