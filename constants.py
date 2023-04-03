from enum import Enum

class GPTModel(Enum):
    """
    Enum class for different GPT models with their corresponding name, token limit, and emoji name
    """
    CHAT_GPT = ('gpt-3.5-turbo', 4096, '3️⃣')
    GPT_4 = ('gpt-4', 8192, '4️⃣')
    def __init__(self, version: str, token_limit: int, emoji_name: str):
        self.version = version
        self.token_limit = token_limit
        self.emoji = emoji_name

### Static messages
WELCOME_MESSAGE = """I am DiscordGPT bot!

A **new channel message** will be set as a **system message**, and all conversation **must go in threads**.

To choose a GPT model start your system message with a model name.
For example,
> GPT-4: You are the world's best assistant. 


To learn more visit https://platform.openai.com/docs/guides/chat
"""
