from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.connectors.ai.open_ai import AzureChatPromptExecutionSettings

import os

class Setup:

     @staticmethod
     def create_kernel()->Kernel:
          """Create instance of kernel
          """
          return Kernel()
     @staticmethod
     def get_settings_from_service_id(kernel:Kernel,service_id:str)->PromptExecutionSettings|AzureChatPromptExecutionSettings:
          agent_v2 = False
          """Recall execution settings of a service using a service id or if agent v2 is True it will create an instance of AzureChatPromptExecutionSettings.

          Args:
               kernel (Kernel): A kernel object.
               service_id (str): service id of the service you want to get execution settings.
          """
          if not agent_v2:
               return kernel.get_prompt_execution_settings_from_service_id(service_id)
          else:
               return AzureChatPromptExecutionSettings(
                    service_id=service_id,
                    max_tokens=1000,
                    temperature=0.5
               )