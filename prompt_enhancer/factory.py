from prompt_enhancer.local_llm import LocalLLMEnhancer

_instance = None

def get_enhancer(provider_type="local", config=None):
    """
    Fabrique (Factory) pour instancier le moteur d'enrichissement de prompts.
    Prêt pour accueillir de futurs adaptateurs (OpenAI, Claude, Ollama local, etc.).
    """
    global _instance
    if provider_type == "local":
        if _instance is None:
            _instance = LocalLLMEnhancer()
        return _instance
    else:
        # Futurs fournisseurs (OpenAI / Claude / etc.)
        raise ValueError(f"Fournisseur d'enrichissement inconnu: {provider_type}")
