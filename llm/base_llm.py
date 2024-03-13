# base_llm.py
import base64
from abc import ABC, abstractmethod

from typing import List, Dict

import discord
import requests

from constants import LLMModel


class LLMException(Exception):
    pass




class LLM(ABC):
    """
    Abstract base class for Language Model (LLM) implementations.
    """

    def __init__(self):
        self.model = None

    @abstractmethod
    async def communicate(self, history: List[discord.Message],
                          model: LLMModel,
                          temperature: float,
                          top_p: float,
                          system_message: str) -> str:
        """
        An abstract method for communicating with a language model using a Discord thread.

        Args:
            history (List[discord.Message]): The Discord message history to use for the communication.
            model (LLMModel): The language model to use for generating the communication.
            temperature (float): The temperature parameter for controlling the randomness of the generated text.
            top_p (float): The nucleus sampling parameter for generating the text.
            system_message (str): The system message to be communicated.

        Returns:
            str: The generated communication message.
        """
        pass

    @abstractmethod
    async def _calculate_tokens(self, content: list[dict[str, str]], model: LLMModel) -> int:
        """
        Calculates the number of tokens required to process a message.

        Args:
            content (str): the message to process.
            model (GPTModel): the OpenAI model to use.

        Returns:
            num_tokens (int): the number of tokens required to process the message.
        """
        pass

    async def collect_payload(self, history: List[discord.Message], model: LLMModel, system_message: str) -> List[Dict]:
        """
        Assembled LLM payload from messages in a Discord thread.

        Args:
            history (List[discord.Message]): The Discord message history to use for the communication.
            model (LLMModel): The language model to use for generating the communication.
            system_message (str): The system message to be communicated.

        Returns:
            str: The generated communication message.
        """
        messages = []
        tokens = 0

        # Add system message
        system_message_content = [{
            'type': 'text',
            'text': system_message
        }]
        tokens += await self._calculate_tokens(system_message_content, model)
        system_message_entry = {'role': 'system', 'content': system_message_content}
        messages.append(system_message_entry)

        reached_token_limit = False

        # Fetches history in reverse order
        for msg in history:
            # Skip configuration messages and system messages
            if msg.system_content != msg.content:
                continue

            entries = []

            # Handle message attachments
            for attachment in msg.attachments:
                content = await self._handle_attachment(attachment)
                tokens += await self._calculate_tokens(content, model)
                if tokens > model.token_limit:
                    reached_token_limit = True
                entries.append({
                    'role': 'assistant' if msg.author.bot else 'user',
                    'content': content
                })

            # Handle actual message content
            if msg.content:
                content = [{'type': 'text', 'text': msg.content}]
                tokens += await self._calculate_tokens(content, model)
                if tokens > model.token_limit:
                    reached_token_limit = True
                entries.append({
                    'role': 'assistant' if msg.author.bot else 'user',
                    'content': content
                })

            if reached_token_limit:
                break

            # Insert at the beginning
            messages.extend(entries)

        return messages

    async def _handle_attachment(self, attachment: discord.Attachment) -> list[dict[str, str]]:
        """
        Handles an attachment by downloading its content and converting it to the appropriate format.
        Args:
            attachment (discord.Attachment): the attachment to handle.
        Returns:
            content (list[dict[str, str]]): the processed attachment content.
        Raises:
            BotGPTException: if the attachment type is unsupported or failed to download.
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
                    'type': 'image_url',
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                }]
            else:
                raise LLMException(f'Failed to download attachment: {response.status_code}')
        else:
            raise LLMException(f'Unsupported attachment type: {content_type}')
