from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.chat_history import ChatHistory

import os

class Agent_Response:
    """Construct Response from agent
    """
    _agent_v2 = False
    def __init__(self, content: ChatMessageContent | str, chat_history:ChatHistory):
        """
        Initializes a new instance of the Alchive_Response class.

        Args:
            content (AsyncIterable[ChatMessageContent] | str ): An asynchronous iterable that provides chat message content.
            chat (ChatHistory): An instance of the ChatHistory class that represents the chat history.
        """
        self._content = content
        self._chat_history = chat_history
        if not self._agent_v2:
            self._chat_history.add_message(content)

    @property
    def response(self) -> str:
        """Parse agent response from content.

        Returns:
            agent response in string.
        """
        if not self._agent_v2:
            return self._content.content
        else:
            return self._content
    
    @property
    def str_chat_history(self) -> str:
        """Convert Chat History into a string.

        Returns:
            Return a string representation of the history.
        """
        return self._chat_history.to_prompt()
    
    @property
    def chat_history(self) -> ChatHistory:
        """A ChatHistory object.

        Returns:
            Return a ChatHistory object
        """
        return self._chat_history
