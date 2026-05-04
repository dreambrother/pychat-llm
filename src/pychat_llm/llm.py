from abc import ABC, abstractmethod


class LLMProvider(ABC):
    @abstractmethod
    def get_response(self, prompt: str) -> str:
        raise NotImplementedError

    def get_welcome_message(self) -> str:
        return "Привет! Я ваш ассистент. Чем могу помочь?"
