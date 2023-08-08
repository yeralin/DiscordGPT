from enum import Enum
from typing import Tuple, List, Dict

import discord
import openai
import requests

import tiktoken


class BotGPTException(Exception):
    pass


class GPTModel(Enum):
    """
    Enum class for different GPT models with their corresponding name, token limit, and emoji name
    """
    CHAT_GPT = ('gpt-3.5-turbo', 4096, True)
    CHAT_GPT_16K = ('gpt-3.5-turbo-16k', 16384, True)
    GPT_4 = ('gpt-4', 8192, True)
    GPT_4_32K = ('gpt-4-32k', 32768, False)

    def __init__(self, version: str, token_limit: int, available: bool):
        self.version = version
        self.token_limit = token_limit
        self.available = available

    @classmethod
    def from_version(cls, version: str):
        """
        Retrieve the GPTModel enum member based on the provided version string.

        Parameters:
            version: The version string to search for in the enum.

        Returns:
            GPTModel: The GPTModel enum member corresponding to the given version.

        Raises:
            ValueError: If the provided version is not found in the enum.
        """
        for member in cls:
            if member.version == version:
                return member
        raise ValueError(f'Non-existing "{version}" version. Available versions are {[m.version for m in cls]}')


class GPT:
    """A class to encapsulate OpenAI GPT related functionalities."""

    DEFAULT_MODEL = GPTModel.CHAT_GPT
    DEFAULT_TEMPERATURE = 1.0
    DEFAULT_TOP_P = 1.0

    @staticmethod
    async def calculate_tokens(msg: str, model: GPTModel) -> int:
        """
        Calculates the number of tokens required to process a message.

        Args:
            msg (str): the message to process.
            model (GPTModel): the OpenAI model to use.

        Returns:
            num_tokens (int): the number of tokens required to process the message.
        """
        try:
            encoding = tiktoken.encoding_for_model(model.version)
            return len(encoding.encode(msg))
        except KeyError:
            raise NotImplementedError(
                f'calculate_tokens() is not presently implemented for model {model.version}'
            )

    @staticmethod
    async def _collect_gpt_payload(thread: discord.Thread) -> Tuple[GPTModel, float, float, List[Dict]]:
        """
        Fetches origin data from the thread and forms message history.

        Args:
            thread (discord.Thread): the thread to fetch messages from.

        Returns:
            model (GPTModel): the OpenAI model extracted from the thread.
            temperature (float): temperature setting for the model.
            top_p (float): top_p setting for the model.
            messages (List[dict]): the message history in the format suitable for GPT.
        """
        starter_message, model_message, temperature_message, top_p_message = [m async for m in
                                                                              thread.history(limit=4,
                                                                                             oldest_first=True)]
        # starter_message is not cached
        if not starter_message:
            starter_message = await thread.parent.fetch_message(starter_message.id)

        # Extract configurations
        from discord_util import DiscordUtil
        model = GPTModel.from_version(DiscordUtil.extract_set_value(model_message))
        temperature = float(DiscordUtil.extract_set_value(temperature_message))
        top_p = float(DiscordUtil.extract_set_value(top_p_message))

        messages = []
        tokens = 0

        # Add GPT's system message
        entry = {'role': 'system', 'content': starter_message.system_content}
        tokens += await GPT.calculate_tokens(starter_message.system_content, model)
        messages.append(entry)

        # Fetches history in reverse order
        async for msg in thread.history():
            if msg in [starter_message, model_message, temperature_message, top_p_message]:
                continue
            content = msg.content
            for attachment in msg.attachments:
                response = requests.get(attachment.url)
                content += response.text
            entry = {
                'role': 'assistant' if msg.author.bot else 'user', 'content': content
            }
            tokens += await GPT.calculate_tokens(content, model)
            if tokens > model.token_limit:
                break
            messages.insert(1, entry)

        return model, temperature, top_p, messages

    @staticmethod
    async def _send_payload(model: GPTModel,
                            temperature: float,
                            top_p: float,
                            messages: List[Dict]) -> str:
        """
        Get response from OpenAI GPT API.

        Args:
            messages (List[dict]): the message history in the format suitable for GPT.
            temperature (float): temperature setting for the model.
            top_p (float): top_p setting for the model.
            model (GPTModel): the OpenAI model extracted from the thread.

        Returns:
            assistant_response (str): the response content from the API.
        """
        response = await openai.ChatCompletion.acreate(
            model=model.version,
            messages=messages,
            temperature=temperature,
            top_p=top_p
        )
        assistant_response = response['choices'][0]['message']['content']
        return assistant_response

    @staticmethod
    async def communicate(thread: discord.Thread) -> str:
        """
        Collects GPT payload for the given thread and sends it to OpenAI chat completion API.

        Args:
            thread (discord.Thread): the thread to fetch messages from.

        Returns:
            gpt_response (str): the generated gpt response.
        """
        try:
            model, temperature, top_p, messages = await GPT._collect_gpt_payload(thread)
            gpt_response = await GPT._send_payload(model, temperature, top_p, messages)
            return gpt_response
        except openai.error.RateLimitError as ex:
            # Render retry button on rate limit
            from discord_util import RetryButton
            await thread.send(ex.user_message, view=RetryButton())
