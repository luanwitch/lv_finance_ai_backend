from abc import ABC, abstractmethod

class BaseProvider(ABC):

    @abstractmethod
    def generate(self, prompt: str):
        """
        Gera uma resposta utilizando um modelo de IA.
        """
        pass