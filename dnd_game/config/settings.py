from typing import Optional
from pydantic import Field, root_validator, DirectoryPath
from pydantic_settings import BaseSettings
from pathlib import Path
from functools import lru_cache

class Settings(BaseSettings):
    """Main settings class that includes all configuration settings"""
    
    # Game-specific settings
    default_rounds: int = Field(default=5, ge=1, description="Default number of rounds to play")
    save_directory: DirectoryPath = Field(
        default=Path("./dnd_game/saves"),
        description="Directory for save files"
    )
    auto_save: bool = Field(default=True, description="Whether to auto-save after each round")
    debug_mode: bool = Field(default=False, description="Enable debug output")

    # Model settings
    openai_api_key: str = Field(..., env="OPENAI_API_KEY", description="OpenAI API key")
    ollama_host: str = Field(default="http://localhost:11434", description="Ollama API host")

    # Default models for different roles
    default_dm_model: str = Field(default="openai|gpt-4", description="Default model for DM agent")
    default_player_model: str = Field(default="ollama|llama2", description="Default model for player agents")
    default_chronicler_model: str = Field(default="openai|gpt-4", description="Default model for chronicler agent")

    # Temperature settings
    default_dm_temperature: float = Field(default=0.7, ge=0.0, le=1.0, description="Default temperature for DM agent")
    default_player_temperature: float = Field(default=0.7, ge=0.0, le=1.0, description="Default temperature for player agents")
    default_chronicler_temperature: float = Field(default=0.3, ge=0.0, le=1.0, description="Default temperature for chronicler agent")

    # Logging settings
    log_level: str = Field(
        default="INFO",
        pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$",  # Updated from 'regex' to 'pattern'
        description="Logging level (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    log_file: Optional[Path] = Field(
        default=None,
        description="Log file path (if None, logs to stdout)"
    )
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log message format"
    )

    # Validators
    @root_validator(pre=True)
    def validate_model_strings(cls, values):
        """Validate all model-related fields"""
        for field_name, value in values.items():
            if field_name.endswith('_model'):
                try:
                    provider, model = value.lower().split('|')
                    if provider not in ['openai', 'ollama']:
                        raise ValueError(f"Unknown provider: {provider}")
                except ValueError:
                    raise ValueError(f"Invalid model string format: {value}. Expected 'provider|model'")
        return values

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        env_nested_delimiter = '__'
        case_sensitive = False
        extra = "ignore"

@lru_cache()
def get_settings() -> Settings:
    """Get settings instance (cached)"""
    return Settings()

if __name__ == "__main__":
    # Example usage
    settings = get_settings()

    print("Game Settings:")
    print(f"Default Rounds: {settings.default_rounds}")
    print(f"Save Directory: {settings.save_directory}")
    print(f"Auto Save: {settings.auto_save}")

    print("\nModel Settings:")
    print(f"DM Model: {settings.default_dm_model}")
    print(f"Player Model: {settings.default_player_model}")
    print(f"Chronicler Model: {settings.default_chronicler_model}")

    print("\nLogging Settings:")
    print(f"Log Level: {settings.log_level}")
    print(f"Log Format: {settings.log_format}")

    # Validate the settings
    try:
        settings.model_dump()
        print("\nSettings validation passed!")
    except Exception as e:
        print(f"\nSettings validation failed: {e}")
