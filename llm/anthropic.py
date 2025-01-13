import base64
from typing import List

import discord
import requests
from anthropic import AsyncAnthropic

from constants import LLMModel, DEFAULT_MAX_TOKENS
from llm.base_llm import LLM, LLMException


class Anthropic(LLM):
    """A class to encapsulate Anthropic API related functionalities."""

    def __init__(self, api_key):
        super().__init__()
        self.client = AsyncAnthropic(api_key=api_key)

    async def communicate(self, history: List[discord.Message],
                          model: LLMModel,
                          temperature: float,
                          top_p: float,
                          system_message: str) -> str:
        """
        An abstract method for communicating with a language model using a Discord thread.

        Args:
            history (List[discord.Message]): The Discord message history to assemble for the communication.
            model (LLMModel): The language model to use for communication.
            temperature (float): The temperature parameter for controlling the randomness of the generated text.
            top_p (float): The nucleus sampling parameter for selecting the most probable tokens.
            system_message (str): The system message to be communicated.

        Returns:
            str: The generated LLM response.
        """
        messages = await self._collect_payload(history, model, system_message)
        messages.pop(0)  # Remove system entry (Anthropic takes it as a separate field)

        response = await self.client.messages.create(
            model=model.version,
            max_tokens=DEFAULT_MAX_TOKENS,
            temperature=temperature,
            top_p=top_p,
            system=system_message,
            messages=messages
        )
        return response.content[0].text

    async def _handle_attachment(self, attachment: discord.Attachment) -> list[dict[str, str]]:
        """
        Handles Discord attachment by downloading its content and converting it to the appropriate format.

        Args:
            attachment (discord.Attachment): the attachment to handle.
        Returns:
            content (list[dict[str, str]]): the processed attachment content.
        Raises:
            LLMException: if the attachment type is unsupported or failed to download.
        """
        content_type = attachment.content_type
        if 'text/plain' in content_type:
            response = requests.get(attachment.url)
            if response.status_code == 200:
                return [{
                    'type': 'text',
                    'text': response.text
                }]
            else:
                raise LLMException(f'Failed to download attachment: {response.status_code}')
        elif content_type in ('image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'):
            response = requests.get(attachment.url)
            if response.status_code == 200:
                # Convert the image content to base64
                base64_image = base64.b64encode(response.content).decode('utf-8')
                return [{
                    'type': 'image',
                    "source": {
                        "type": "base64",
                        "media_type": content_type,
                        "data": base64_image
                    }
                }]
            else:
                raise LLMException(f'Failed to download attachment: {response.status_code}')
        else:
            raise LLMException(f'Unsupported attachment type: {content_type}')

    async def _calculate_tokens(self, role: str, content: list[dict[str, str]], model: LLMModel) -> int:
        """
        Calculates the number of tokens from content for given model.

        Args:
            role (str): who sends the message.
            content (str): the message to process.
            model (GPTModel): the LLM model to calculate tokens for.

        Returns:
            num_tokens (int): the number of tokens calculated from supplied content.
        """
        response = await self.client.messages.count_tokens(
                model=model.version,
                messages=[{
                    'role': role,
                    'content': content
                }]
            )
        return response.input_tokens
