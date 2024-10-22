from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.chat_history import ChatHistory



class Alchive_Response:
    """Construct Response from agent
    """
    def __init__(self, content: ChatMessageContent, chat:ChatHistory):
        """
        Initializes a new instance of the Alchive_Response class.

        Args:
            content (AsyncIterable[ChatMessageContent]): An asynchronous iterable that provides chat message content.
            chat (ChatHistory): An instance of the ChatHistory class that represents the chat history.
        """
        self._content = content
        self._chat = chat

    @property
    def response(self) -> str:
        """Parse agent response from content.

        Returns:
            agent response in string.
        """
        return self._content.content
    
    @property
    def chat_history(self) -> str:
        """Convert Chat History into a string.

        Returns:
            Return a string representation of the history.
        """
        self._chat.add_message(self._content)
        return self._chat.to_prompt()