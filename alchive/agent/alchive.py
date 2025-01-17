
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.memory.semantic_text_memory import SemanticTextMemory
from semantic_kernel.connectors.memory.azure_cognitive_search import AzureCognitiveSearchMemoryStore
from semantic_kernel.connectors.ai.open_ai.services.azure_text_embedding import AzureTextEmbedding
from semantic_kernel.functions.kernel_plugin import KernelPlugin
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.connectors.ai.open_ai import AzureChatPromptExecutionSettings
from semantic_kernel.core_plugins import ConversationSummaryPlugin
from semantic_kernel.prompt_template import InputVariable, PromptTemplateConfig
from semantic_kernel.functions import KernelArguments
from semantic_kernel.contents.chat_message_content import ChatMessageContent 
from semantic_kernel.contents.utils.author_role import AuthorRole

from alchive.functions import ExtractPDF
from alchive.utils import Prompts, Agent_Response
from alchive.agent.setup import Setup
from alchive.AlchivePlugins.MemoryPlugin.memory import MemoryPlugin
from alchive.functions import StorageAccount

import os
import json

agent_token_response = 1000

class Alchive:
    """
        Alchive is an AI Agent bot.
    """
    _instance = None
    _chat_service_id = "alchive"
    _embedding_service_id = "embedding"
    _is_streaming = False
    _index_name = ""
    _current_dir = os.path.dirname(os.path.abspath(__file__))
    _plugin = "AlchivePlugins"
    _agent_v2 = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Alchive, cls).__new__(cls, *args, **kwargs)
            cls._agent_kernel:Kernel = None
            cls._initiator_kernel:Kernel = None
            cls._agent = None
            cls._initiator = None
            cls._memory_base:AzureCognitiveSearchMemoryStore = None
            cls._memory:SemanticTextMemory = None
            cls._embedding_service = None
            cls._storage_account:StorageAccount = None
        return cls._instance
    
    def initialize_kernel(self)->str:
        """Initialize kernel and its services.

        Returns:
            Agent id
        """
        if not self._agent_kernel:
            self._agent_kernel = Setup.create_kernel() # crete an instance of Kernel object
            self._embedding_service = AzureTextEmbedding(service_id=self._embedding_service_id) # create embedding service
            self._agent_kernel.add_service(service=AzureChatCompletion(service_id=self._chat_service_id)) # add chat completion service to the kernel
            self._agent_kernel.add_service(self._embedding_service) # add text embedding service to the kernel
            settings = Setup.get_settings_from_service_id(self._agent_kernel,self._chat_service_id) # getting execution setting of a service using service id.
            if not self._agent_v2:
                settings.function_choice_behavior = FunctionChoiceBehavior.Auto() # setting up Fucntion calling behavior of the agent
            self._initialize_storage_account() #initialize storage account
            self._initialize_memory_base() # initialize memory base
            self._agent_kernel.add_plugin(MemoryPlugin(memory=self._memory , storage_account=self._storage_account), plugin_name="Memory") # adding a Native function plugin to the Kernel that retrieve memory to the memory base
            # self._kernel.add_plugin(TextMemoryPlugin(memory=self._memory), plugin_name="memory")
            agent_id = self._create_agent(settings) # creating agent

        if not self._initiator_kernel:
            self._initiator_kernel = Setup.create_kernel()
            self._initiator_kernel.add_service(service=AzureChatCompletion(service_id=self._chat_service_id))
            if not self._initiator:
                self._initiator = self._initiator_kernel.add_plugin(parent_directory=os.path.normpath(os.path.join(self._current_dir, '..', self._plugin)), plugin_name="ChatPlugin")
                
        return agent_id
    
    def _create_agent(self,settings)->str:
        """Create instance of ChatCompletionAgent.
            
        Args:
            settings (PromptExecutionSettings|AzureChatPromptExecutionSettings): The execution settings for the agent.
        """
        if not self._agent:
            if not self._agent_kernel:
                self.initialize_kernel()
            # Instance of ChatCompletion object
            if not self._agent_v2:
                self._agent = ChatCompletionAgent(service_id=self._chat_service_id,
                                                kernel=self._agent_kernel,
                                                instructions=Prompts.AGENT_PROMPTS,
                                                name=self._chat_service_id,
                                                execution_settings=settings
                                                )
                return self._agent.id
            else:
                self._agent = ChatCompletionAgentV2(service_id=self._chat_service_id,
                                                   kernel=self._agent_kernel,
                                                   instructions=Prompts.AGENT_V2_PROMPTS,
                                                   settings=settings)
            
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

    def _initialize_storage_account(self)-> None:
        if not self._storage_account:
            self._storage_account = StorageAccount(name=os.getenv("STORAGE_ACCOUNT_NAME"),
                                                   container_name=os.getenv("CONTAINER_NAME"))
    
    async def invoke_agent_alchive(self, input:str, chat:ChatHistory)->Agent_Response:
        """Invoke the agent with the user input.
        
        Args:
            input (str): User question or query.
            chat (ChatHistory): Chat History

        Returns:
            An async iterable of ChatMessageContent.
        """
        chat.add_user_message(input)
        if not self._agent_v2:
            string_to_bool = {"True" : True, "False": False }
            is_question_biology_related = self._initiator["QuestionChecker"]
            response_to_non_bio_query = self._initiator["NoResponse"]
            
            is_related = await self._initiator_kernel.invoke(is_question_biology_related,
                                                             KernelArguments(user_input = input, chat_history = chat))
            print(f"Is question Related to Biology? {is_related}")
            if not string_to_bool[str(is_related)]:
                response = await self._initiator_kernel.invoke(response_to_non_bio_query,
                                                               KernelArguments(user_query = input))
                print(str(response))
                content = ChatMessageContent(
                    role=AuthorRole.ASSISTANT,
                    content=str(response)
                )
                return Agent_Response(content,chat)
            else:
                # invoke the agent
                async for content in self._agent.invoke(chat):
                    #print(f"# {content.role} - {content.name or '*'}: '{content.content}'")
                    return Agent_Response(content,chat)
        else:
            response, history = await self._agent.invoke_v2(input,chat)
            return Agent_Response(response,history)
    async def upload_file(self)->None:
        """Upload the file and index to memory base
        """
        memory = self._memory
        files = self._storage_account.get_list_of_blobs()
        
        for file in files:

            
            metadata = {}
            metadata['file_name'] = file.name
            metadata['module_name'] = self._storage_account.get_file_metadata(metadata_name="module_name", blob=file)
            
            pdf_content_bytes = self._storage_account.get_download_blob(file)
            pdf_pages = ExtractPDF.extract_pages(pdf_bytes=pdf_content_bytes)
            
            for i, page in enumerate(pdf_pages, start=1):
                if page:
                    await memory.save_information(
                                                collection="genbiokb",
                                                text=page,
                                                id=f"{i}-{file.name}",
                                                additional_metadata=str(metadata)
                                                )
                    print(f"page {i} has been uploaded.")

    def add_capabilities(self, plugins: list[KernelPlugin] | dict[str, KernelPlugin | object])->dict[str, KernelPlugin]:
        """Add list/dictionary of plugins to add in the kernel

        Args:
            plugins: (list[KernelPlugin] | dict[str, KernelPlugin | object]) list of KernelPlugin object | dictionary of KernelPlugin or object.
        Returns:
            (dict[str, KernelPlugin]) - Dictionary of all plugins in the kernel
        """
        self._agent_kernel.add_plugins(plugins)
        return self._agent_kernel.plugins
    
    def save_history_to_storage(self, file_name:str, chat: dict):
        
        if self._storage_account.is_blob_exist(file_name):
            existing_history = json.loads(self._storage_account.download_blob(file_name))
        else:
            existing_history = []
        
        existing_history.append(chat)
        
        try:
            self._storage_account.save_to_file(file_name,
                                               json.dumps(existing_history)
                                               )
        except Exception as e:
            print(e)
    def download_history_from_storage(self, file_name):
        isExist = self._storage_account.is_blob_exist(file_name)
        print(isExist)
        if isExist:
            return json.loads(self._storage_account.download_blob(file_name))
        else:
            return []
            

class ChatCompletionAgentV2:
    def __init__(self,
                 service_id:str,
                 kernel:Kernel,
                 instructions:str,
                 settings:AzureChatPromptExecutionSettings):
        self._service_id = service_id
        self._kernel = kernel
        
        self._agent_v2 = self._kernel.add_function(
            function_name = "AlchiveV2",
            plugin_name = "AgentV2",
            prompt_template_config = PromptTemplateConfig(
                template=instructions,
                name="alchive",
                template_format="semantic-kernel",
                input_variables=[InputVariable(name="user_input", description="user input question", is_required=True),
                                 InputVariable(name="chat_history", description="chat history", is_required=True)],
                execution_settings=settings
            )
        )
    async def invoke_v2(self, input:str, chat_history:ChatHistory):
        arguments = KernelArguments(user_input = input, chat_history=chat_history)
        response = await self._kernel.invoke(self._agent_v2, arguments)
        if response:
            chat_history.add_assistant_message(str(response))
        
        return str(response), chat_history

    