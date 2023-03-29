from enum import Enum
from typing import List, Dict
from collections import deque

import copy

from .message_entry import MessageEntry


class Role(Enum):
    """
    An enum that represents the roles of a message.

    Attributes:
        ASSISTANT (str): The role of the assistant.
        USER (str): The role of the user.
        SYSTEM (str): The role of the system.
    """
    ASSISTANT = 'assistant'
    USER = 'user'
    SYSTEM = 'system'


class TokenizedMessageLimiterException(Exception):
    """
    An exception raised when there is an error with TokenizedMessageLimiter.
    """
    pass


class TokenizedMessageLimiter:
    """
    A class that stores messages and prunes its entries upon reaching a token limit.

    Attributes:
        limit (int): The maximum number of tokens allowed in the data structure.
        message_history (deque): A deque containing the message history.
        token_count (int): The current number of tokens in the data structure.
        system_message (dict): A dictionary containing the system message.
        system_message_tokens (int): The number of tokens in the system message.
    """

    def __init__(self, limit: int = 4096):
        """
        Initializes a TokenLimiter object with the given token limit.

        Args:
            limit (int): The maximum number of tokens allowed in the data structure.
        """
        self.limit: int = limit
        self.message_history: deque[MessageEntry] = deque()
        self.token_count: int = 0
        # Initialize default system message
        self.system_message: MessageEntry = MessageEntry(
            Role.SYSTEM,
            'You are a helpful assistant that answers messages accurately and concisely')
        self.limit -= self.system_message.tokens

    def set_system_message(self, new_system_msg: str) -> None:
        """
        Sets new system message for the bot.

        Args:
            new_system_msg (str): The new system message.
        """
        if not new_system_msg:
            raise TokenizedMessageLimiterException(
                'System message cannot be empty')
        self.limit += self.system_message.tokens
        self.system_message = MessageEntry(Role.SYSTEM, new_system_msg)
        self.limit -= self.system_message.tokens

    def add_message(self, msg: str, role: Role) -> None:
        """
        Adds a message to the message history and updates the number of tokens.

        Args:
            msg (str): The message text.
            role (Role): The role of the message sender.
        """
        entry = MessageEntry(role, msg)
        self.message_history.append(entry)
        self.token_count += entry.tokens
        if self.token_count > self.limit:
            _ = self._prune_messages()

    def clean_messages(self):
        """
        Cleans message history and resets the system message.
        """
        _ = self._prune_messages(0)
        self.set_system_message(self.system_message.msg['content'])

    def serialize_messages(self) -> List[str]:
        """
        Serializes stored messages into a single list
        """
        messages = [self.system_message.msg]
        messages.extend([entry.msg for entry in self.message_history])
        return messages

    def _prune_messages(self, limit: int = None) -> List[MessageEntry]:
        """
        Removes messages from the message history until the token count is below the limit.

        Args:
            limit (int, optional): The maximum limit of token count.

        Returns:
            A list of the removed messages.
        """
        if limit is None:
            limit = self.limit
        pruned_messages: List[MessageEntry] = []
        while self.token_count > self.limit:
            removed_entry = self.message_history.popleft()
            self.token_count -= removed_entry.tokens
            pruned_messages.append(removed_entry)
        return pruned_messages

    def __deepcopy__(self, memo: Dict) -> 'TokenizedMessageLimiter':
        """
        Returns a deep copy of the TokenLimiter object.

        Args:
            memo (Dict[int, Any]): A dictionary to track the copied objects.

        Returns:
            A deep copy of the TokenLimiter object.
        """
        memo[id(self)] = self
        new_obj = TokenizedMessageLimiter(limit=self.limit)
        new_obj.message_history = copy.deepcopy(self.message_history, memo)
        new_obj.token_count = self.token_count
        new_obj.system_message = copy.deepcopy(self.system_message, memo)
        return new_obj
