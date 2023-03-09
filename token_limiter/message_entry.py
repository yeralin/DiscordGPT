from _ast import Dict

import tiktoken


class MessageEntry:
    """
    A data model that contains the message and the number of tokens in that message.

    Attributes:
        message (dict): A dictionary containing the message data.
        tokens (int): The number of tokens in the message.
    """

    def __init__(self, role: 'Role', content: str,
        model: str = 'gpt-3.5-turbo'):
        self.msg: Dict[str, str] = {'role': role.value, 'content': content}
        self.tokens: int = self._calculate_tokens(model)

    def _calculate_tokens(self, model: str) -> int:
        """
        Calculates the number of tokens in the message.

        Args:
            model (str): The tokenization model to use.

        Returns:
            The number of tokens in the message.
        """
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            encoding = tiktoken.get_encoding('cl100k_base')
        if model == 'gpt-3.5-turbo':
            num_tokens = 4
            for key, value in self.msg.items():
                num_tokens += len(encoding.encode(value))
                if key == 'name':
                    num_tokens += -1
            num_tokens += 2
            return num_tokens
        else:
            raise NotImplementedError(
                f'calculate_tokens() is not presently implemented for model {model}')
