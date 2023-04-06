import discord
import openai

from gpt import construct_gpt_payload, GPTModel


async def safe_send(ctx: discord.abc.Messageable, text: str) -> None:
    """
    Sends a message to the given channel or user, breaking it up if necessary to avoid Discord's message length limit.
    """
    while len(text) > 2000:
        break_pos = text.rfind('\n', 0, 2000)
        await ctx.send(text[:break_pos])
        text = text[break_pos:]
    await ctx.send(text)


async def collect_and_send(thread: discord.Thread):
    """
    Collects history messages from the thread, constructs a GPT payload, and sends the assistant's response.

    This function is responsible for collecting messages from the given thread, constructing a payload
    to send to the GPT model, and sending the assistant's response back to the thread.

    If a RateLimitError occurs, it renders a RetryButton for retrying the process.

    Args:
        thread (discord.Thread): The thread where messages are collected and the assistant's response is sent.

    Raises:
        openai.error.RateLimitError: If the rate limit is exceeded for the GPT API call.
    """
    try:
        async with thread.typing():
            messages, model = await construct_gpt_payload(thread)
            response = await openai.ChatCompletion.acreate(
                model=model.version,
                messages=messages
            )
            assistant_response = response['choices'][0]['message']['content']
        await safe_send(thread, assistant_response)
    except openai.error.RateLimitError as ex:
        # Render retry button on rate limit
        await thread.send(ex.user_message, view=RetryButton())


class RetryButton(discord.ui.View):
    """
    This class is invoked when `openai.error.RateLimitError` is thrown in `collect_and_send` method.
    It is responsible for rendering retry button and handling the retry mechanism.
    """

    @discord.ui.button(label="Retry", style=discord.ButtonStyle.primary)
    async def retry_callback(self, interaction: discord.Interaction, _: discord.ui.Button):
        """
        This function handles user press on the retry button. It deletes the original retry message,
            and re-tries to send payload.
        Args:
            interaction: The interaction object which contains the context of the chat
            _: button object, ignored
        """
        await interaction.message.delete()
        await collect_and_send(interaction.channel)


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
