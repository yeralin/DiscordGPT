import base64
import math
from io import BytesIO
from typing import List, Dict

import discord
import requests
import tiktoken
from PIL import Image
from openai import AsyncOpenAI

from constants import LLMModel
from llm.base_llm import LLM, LLMException


class OpenAI(LLM):
    """A class to encapsulate OpenAI GPT related functionalities."""

    def __init__(self, api_key):
        super().__init__()
        self.client = AsyncOpenAI(api_key=api_key)

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
        response = await self.client.chat.completions.create(
            model=model.version,
            messages=messages,
            temperature=temperature,
            top_p=top_p,
            max_tokens=4096 if model == LLMModel.GPT_4_O else None
        )
        gpt_response = response.choices[0].message.content
        return gpt_response

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
                    'type': 'image_url',
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
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
        try:
            encoding = tiktoken.encoding_for_model(model.version)
            tokens = 0
            for entry in content:
                if entry['type'] == 'text':
                    tokens += len(encoding.encode(entry['text']))
                elif entry['type'] == 'image_url':
                    # Calculating tokens for image as per
                    # https://platform.openai.com/docs/guides/vision/calculating-costs
                    _, base64_image = entry['image_url']['url'].split(",", 1)
                    image = Image.open(BytesIO(base64.b64decode(base64_image)))
                    h = math.ceil(image.height / 512)
                    w = math.ceil(image.width / 512)
                    n = w * h
                    tokens += 85 + 170 * n
            return tokens
        except KeyError:
            raise NotImplementedError(
                f'_calculate_tokens() is not presently implemented for model {model.version}'
            )
