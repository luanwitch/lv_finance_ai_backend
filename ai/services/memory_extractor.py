from ai.memory.memory_service import MemoryService

class MemoryExtractor:

    KEYWORDS = {
        "goal": [
            "quero",
            "objetivo",
            "meta",
            "pretendo"
        ],

        "debt": [
            "dívida",
            "devendo"
        ],

        "income": [
            "salário",
            "recebo",
            "ganho"
        ],

        "expense": [
            "gasto",
            "despesa",
            "pago"
        ]
    }

    @classmethod
    def process(cls, user, text):

        lower = text.lower()

        for memory_type, words in cls.KEYWORDS.items():

            if any(word in lower for word in words):

                MemoryService.save(
                    user=user,
                    text=text,
                    memory_type=memory_type,
                    importance=8
                )

                return True

        return False