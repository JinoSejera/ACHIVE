# Define a sample plugin for the sample
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.memory.semantic_text_memory_base import SemanticTextMemoryBase
from typing import Annotated
import json
import logging
import os

from alchive.functions import StorageAccount
logger: logging.Logger = logging.getLogger(__name__)

class MemoryPlugin:
    """A Recall Plugin used to recall knowledge"""

    RELEVANCE_SCORE = 0.6
    INDEX_NAME = os.getenv("INDEX_NAME")
    LIMIT = 3
    def __init__(self, memory:SemanticTextMemoryBase, storage_account:StorageAccount):
        self._storage_account = storage_account
        self._memory = memory

    @kernel_function(description="Fetch and Provides a list of knowledge related to Biology retrieved from memory.", name="genbio")
    async def memories(self,
                 user_ask: Annotated[str, "What user ask to recall"]
                 ) -> Annotated[str, "Returns all the memory retrieve in the knowledge base."]:
        print(f"what is asked: {user_ask}")


        results = await self._memory.search(
        collection=self.INDEX_NAME,
        query=user_ask,
        limit=self.LIMIT,
        min_relevance_score=self.RELEVANCE_SCORE,
        )
        if results is None or len(results) == 0:
            logger.warning(f"Memory not found in collection: {self.INDEX_NAME}")
            return ""
        # print(f"memory: {results[0].text}\n")
        # print(f"source: {results[0].additional_metadata}")
        search_results = []
        for result in results:
            metadata = result.additional_metadata
            metadata = metadata.replace("'", '"')
            dict_metadata = json.loads(metadata)
            
            downloadable_link = self._storage_account.get_file_downloadable_link(dict_metadata['file_name'])
            search_results.append({
                "search_query": user_ask,
                "search_memory_result":result.text,
                "seach_result_reference": dict_metadata['module_name'],
                "downloadable_link": downloadable_link
            })
        print(search_results)

        # return results[0].text if self.LIMIT == 1 else json.dumps([r.text for r in results])
        return str(search_results)
