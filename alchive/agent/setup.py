from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings

class Setup:

    @staticmethod
    def create_kernel()->Kernel:
         """Create instance of kernel
         """
         return Kernel()
    @staticmethod
    def recall_settings_from_service_id(kernel:Kernel,service_id:str)->PromptExecutionSettings:
         """Recall execution settings of a service using a service id.

         Args:
            kernel (Kernel): A kernel object.
            service_id (str): service id of the service you want to get execution settings.
         """
         return kernel.get_prompt_execution_settings_from_service_id(service_id)