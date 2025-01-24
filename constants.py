# Constants
from enum import Enum


class LLMModel(Enum):
    """
    Base class for LLM model enums.
    """
    GPT_4_O = ('OpenAI', 'gpt-4o', 128*1000, True)
    CLAUDE_3_5_SONNET = ('Anthropic', 'claude-3-5-sonnet-20240620', 200*1000, True)

    def __init__(self, vendor: str, version: str, token_limit: int, available: bool):
        self.vendor = vendor
        self.version = version
        self.token_limit = token_limit
        self.available = available

    @classmethod
    def from_version(cls, version: str):
        """
        Retrieve the LLMModel enum member based on the provided version string.
        Parameters:
            version: The version string to search for in the enum.
        Returns:
            LLMModel: The LLMModel enum member corresponding to the given version.
        Raises:
            ValueError: If the provided version is not found in the enum.
        """
        for member in cls:
            if member.version == version:
                return member
        raise ValueError(f'Non-existing "{version}" version. Available versions are {[m.version for m in cls]}')


WELCOME_MESSAGE = """I am DiscordGPT bot!

A **new channel message** will be set as a **system message**, and all conversation **must go in threads**.

To choose a GPT model start your system message with a model name.
For example,
> GPT-4: You are the world's best assistant. 


To learn more visit https://platform.openai.com/docs/guides/chat
"""

DEFAULT_SYSTEM_MESSAGE = """You are a helpful assistant."""

DEFAULT_MODEL = LLMModel.CLAUDE_3_5_SONNET
DEFAULT_TEMPERATURE = 1.0
DEFAULT_TOP_P = 1.0
DEFAULT_MAX_TOKENS = 4096
