
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.memory.semantic_text_memory import SemanticTextMemory
from semantic_kernel.connectors.memory.azure_cognitive_search import AzureCognitiveSearchMemoryStore
from semantic_kernel.connectors.ai.open_ai.services.azure_text_embedding import AzureTextEmbedding
from semantic_kernel.functions.kernel_plugin import KernelPlugin

from alchive.functions import ExtractPDF
from alchive.utils import Prompts, Agent_Response
from alchive.agent.setup import Setup
from alchive.AlchivePlugins.MemoryPlugin.memory import MemoryPlugin

import os

class Alchive:
    """
        Alchive is an AI Agent bot.
    """
    _instance = None
    _chat_service_id = "alchive"
    _embedding_service_id = "embedding"
    _is_streaming = False
    _index_name = ""
    _agent_token_response = 1000

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Alchive, cls).__new__(cls, *args, **kwargs)
            cls._kernel:Kernel = None
            cls._agent = None
            cls._memory_base:AzureCognitiveSearchMemoryStore = None
            cls._memory:SemanticTextMemory = None
            cls._embedding_service = None
        return cls._instance
    
    def initialize_kernel(self)->str:
        """Initialize kernel and its services.

        Returns:
            Agent id
        """
        if not self._kernel:
            self._kernel = Setup.create_kernel() # crete an instance of Kernel object
            self._embedding_service = AzureTextEmbedding(service_id=self._embedding_service_id) # create embedding service
            self._kernel.add_service(service=AzureChatCompletion(service_id=self._chat_service_id)) # add chat completion service to the kernel
            self._kernel.add_service(self._embedding_service) # add text embedding service to the kernel
            settings = Setup.recall_settings_from_service_id(self._kernel,self._chat_service_id) # getting execution setting of a service using service id.
            settings.function_choice_behavior = FunctionChoiceBehavior.Auto() # setting up Fucntion calling behavior of the agent
            settings.extension_data = {"max_tokens":self._agent_token_response}
            self._initialize_memory_base() # initialize memory base
            self._kernel.add_plugin(MemoryPlugin(memory=self._memory), plugin_name="memory") # adding a Native function plugin to the Kernel that retrieve memory to the memory base
            # self._kernel.add_plugin(TextMemoryPlugin(memory=self._memory), plugin_name="memory")
            id = self._create_agent(settings) # creating agent
            return id 
    def _create_agent(self,settings)->str:
        """Create instance of ChatCompletionAgent.
            
        Args:
            settings (PromptExecutionSettings): The execution settings for the agent.
        """
        if not self._agent:
            if not self._kernel:
                self.initialize_kernel()
            # Instance of ChatCompletion object
            self._agent = ChatCompletionAgent(service_id=self._chat_service_id,
                                            kernel=self._kernel,
                                            instructions=Prompts.AGENT_PROMPTS,
                                            name=self._chat_service_id,
                                            execution_settings=settings
                                            )
            return self._agent.id
    def _initialize_memory_base(self)->None:
        """Initialize memory base
        """
        if not self._memory and not self._memory_base:
            # instance of AzureCognitiveSearchMemoryStore as memory base where to retrieve memory
            self._memory_base = AzureCognitiveSearchMemoryStore(
                vector_size=1536,
                search_endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
                admin_key=os.getenv("AZURE_SEARCH_ADMIN_KEY")
            )
            # instance of SemanticTextMemory
            self._memory = SemanticTextMemory(storage=self._memory_base,
                                              embeddings_generator=self._embedding_service)

    async def invoke_agent_alchive(self, input:str, chat:ChatHistory)->Agent_Response:
        """Invoke the agent with the user input.
        
        Args:
            input (str): User question or query.
            chat (ChatHistory): Chat History

        Returns:
            An async iterable of ChatMessageContent.
        """
        chat.add_user_message(input)
        # invoke the agent
        async for content in self._agent.invoke(chat):
            #print(f"# {content.role} - {content.name or '*'}: '{content.content}'")
            return Agent_Response(content,chat)
        
    async def upload_file(self, file_path: str)->None:
        """Upload the file and index to memory base

        Args:
            file_path: (str) path of the file
        """
        memory = self._memory

        pdf_pages = ExtractPDF.extract_pages(file_path=file_path)

        for i, page in enumerate(pdf_pages, start=1):
            source = {}
            source["source"] = file_path
            await memory.save_information(collection="genbio",
                                    text=page,
                                    id=f"{i}-genbio",
                                    additional_metadata=str(source))
            print(f"page {i} has been uploaded.")

    def add_capabilities(self, plugins: list[KernelPlugin] | dict[str, KernelPlugin | object])->dict[str, KernelPlugin]:
        """Add list/dictionary of plugins to add in the kernel

        Args:
            plugins: (list[KernelPlugin] | dict[str, KernelPlugin | object]) list of KernelPlugin object | dictionary of KernelPlugin or object.
        Returns:
            (dict[str, KernelPlugin]) - Dictionary of all plugins in the kernel
        """
        self._kernel.add_plugins(plugins)
        return self._kernel.plugins
