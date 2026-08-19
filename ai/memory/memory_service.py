from ai.embeddings.embedding_service import EmbeddingService
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from ai.models import Memory

class MemoryService:

    @classmethod
    def save(cls, user, text, memory_type="general", importance=5):

        vector = EmbeddingService.embed(text)

        Memory.objects.create(
            user=user,
            content=text,
            memory_type=memory_type,
            importance=importance,
            embedding=vector
        )

    @classmethod
    def all(cls, user):

        return Memory.objects.filter(user=user)


    @classmethod
    def search(cls, user, query, limit=3):

        query_vector = EmbeddingService.embed(query)

        memories = Memory.objects.filter(user=user)

        results = []

        for memory in memories:

            score = cosine_similarity(
                [query_vector],
                [memory.embedding]
            )[0][0]

            results.append({
                "text": memory.content,
                "type": memory.memory_type,
                "importance": memory.importance,
                "score": score
            })

        results.sort(
            key=lambda x: x["score"],
            reverse=True
        )

        return results[:limit]

    
    # Criando méthodo de contexto::
    @classmethod
    def get_context(cls, user, query):

        memories = cls.search(user, query)

        return "\n".join(
            f"- [{m['type']}] {m['text']}"
            for m in memories
        )
        