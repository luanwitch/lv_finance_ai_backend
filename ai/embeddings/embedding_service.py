from langchain_ollama import OllamaEmbeddings


class EmbeddingService:

    embeddings = OllamaEmbeddings(
        model="nomic-embed-text:latest"
    )

    @classmethod
    def embed(cls, text):

        return cls.embeddings.embed_query(text)