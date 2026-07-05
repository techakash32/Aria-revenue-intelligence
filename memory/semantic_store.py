# memory/semantic_store.py
from datetime import datetime, timezone

import chromadb
from chromadb.utils import embedding_functions


class SemanticMemory:
    def __init__(self):
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.ef = embedding_functions.DefaultEmbeddingFunction()
        self.collection = self.client.get_or_create_collection(
            name="past_decisions",
            embedding_function=self.ef
        )

    def store_decision(self, situation: str, action: str, outcome: str):
        """
        Store a past decision as plain text.
        Outcome is manually recorded — no automatic causal inference.
        """
        doc = f"Situation: {situation} | Action taken: {action} | Outcome: {outcome}"
        self.collection.add(
            documents=[doc],
            ids=[f"decision_{datetime.now(timezone.utc).timestamp()}"]
        )

    def retrieve_similar(self, current_situation: str, n_results: int = 3) -> list:
        """
        Semantic search — find past situations similar to this one.
        Returns plain text for the agent to read as context.
        """
        results = self.collection.query(
            query_texts=[current_situation],
            n_results=n_results
        )
        return results["documents"][0] if results["documents"] else []
