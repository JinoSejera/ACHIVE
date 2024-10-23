# Define a sample plugin for the sample
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.memory.semantic_text_memory_base import SemanticTextMemoryBase
from typing import Annotated
import json
import logging

logger: logging.Logger = logging.getLogger(__name__)

class MemoryPlugin:
    """A Recall Plugin used to recall knowledge"""

    RELEVANCE_SCORE = 0.6
    INDEX_NAME = "genbio"
    LIMIT = 1
    def __init__(self, memory:SemanticTextMemoryBase):
        self._memory = memory

    @kernel_function(description="Provides a list of knowledge related to Biology retrieved from memory.")
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

        result = {
            "search_query": user_ask,
            "memory":results[0].text,
            "referecnce": results[0].additional_metadata
        }
        print(result)

        # return results[0].text if self.LIMIT == 1 else json.dumps([r.text for r in results])
        return str(result)
