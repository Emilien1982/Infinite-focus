from abc import ABC, abstractmethod

class BasePromptEnhancer(ABC):
    """
    Interface abstraite pour les moteurs d'enrichissement de prompts sonores.
    Permet de remplacer ou d'ajouter facilement un nouveau fournisseur (LLM local, OpenAI, Claude, Ollama, etc.)
    sans modifier l'application.
    """
    @abstractmethod
    def enrich(self, prompt: str) -> str:
        """
        Enrichit et texture un prompt sonore.
        Le résultat doit TOUJOURS être renvoyé en anglais, quelle que soit la langue d'origine.
        """
        pass
