from enum import Enum

MODEL_MESSAGE_REGEX = r'^(GPT): (.+)$'
class GPTModel(Enum):
    """
    Enum class for different GPT models with their corresponding names and token limits.
    """
    CHAT_GPT = ('gpt-3.5-turbo', 4096)
    GPT_4 = ('gpt-4', 8192)
    def __init__(self, version: str, token_limit: int):
        self.version = version
        self.token_limit = token_limit

### Static messages
WELCOME_MESSAGE = """I am DiscordGPT bot!

A **new channel message** will be set as a **system message**, and all conversation **must go in threads**.

To choose a GPT model start your system message with a model name.
For example,
> GPT-4: You are the world's best assistant. 


To learn more visit https://platform.openai.com/docs/guides/chat
"""
