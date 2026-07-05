import os

class Provider:
    def __init__(self, name: str, url: str, env_key: str):
        self.name = name
        self.url = url
        self.env_key = env_key

    def get_api_keys(self) -> list[str]:
        """Read the API key(s) from the environment variable.

        The project requires supporting MULTIPLE keys per provider (to rotate
        when one hits its quota). Convention: keys are separated by commas.
        Example in .env:  OPENROUTER_API_KEY=key1,key2,key3
        """
        raw_value = os.getenv(self.env_key)
        if not raw_value:
            return []
        return [key.strip() for key in raw_value.split(",") if key.strip()]


PROVIDERS: dict[str, Provider] = {
    "openrouter": Provider(
        "openrouter",
        "https://openrouter.ai/api/v1",
        "OPENROUTER_API_KEY",
    ),
    "groq": Provider(
        "groq",
        "https://api.groq.com/openai/v1",
        "GROQ_API_KEY",
    ),
    "mistral": Provider(
        "mistral",
        "https://api.mistral.ai/v1",
        "MISTRAL_API_KEY",
    ),
    "gemini": Provider(
        "gemini",
        "https://generativelanguage.googleapis.com/v1beta/openai",
        "GEMINI_API_KEY",
    ),
}


def get_provider(name: str) -> Provider:
    if name not in PROVIDERS:
        raise ValueError(
            f"Unknown provider '{name}'."
        )
    return PROVIDERS[name]
