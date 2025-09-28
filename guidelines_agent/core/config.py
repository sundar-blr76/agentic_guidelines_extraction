# config.py
"""
Configuration Management for Guidelines Agent
============================================

Centralized configuration for LLM providers, models, and application settings.
"""

import os
from typing import Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass

# Legacy PostgreSQL Database Configuration for backward compatibility
DB_CONFIG = {
    "host": "192.168.29.69",
    "port": "5432",
    "dbname": "guidelines",
    "user": "postgres",
    "password": "postgres",
}


class LLMProvider(Enum):
    """Supported LLM providers"""
    GEMINI = "gemini"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    MOCK = "mock"


@dataclass
class LLMConfig:
    """Configuration for LLM providers"""
    provider: LLMProvider
    model: str
    temperature: float = 0.1
    max_tokens: Optional[int] = None
    api_key_env_var: str = ""


class Config:
    """Application configuration management"""
    
    # Legacy support
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///guidelines.db")
    GENERATIVE_MODEL = "models/gemini-pro-latest"  # Using latest available model
    
    # LLM Provider Configurations
    LLM_CONFIGS = {
        LLMProvider.GEMINI: LLMConfig(
            provider=LLMProvider.GEMINI,
            model="models/gemini-pro-latest",
            temperature=0.1,
            max_tokens=8192,
            api_key_env_var="GEMINI_API_KEY"
        ),
        LLMProvider.OPENAI: LLMConfig(
            provider=LLMProvider.OPENAI,
            model="gpt-3.5-turbo",
            temperature=0.1,
            max_tokens=4096,
            api_key_env_var="OPENAI_API_KEY"
        ),
        LLMProvider.ANTHROPIC: LLMConfig(
            provider=LLMProvider.ANTHROPIC,
            model="claude-3-haiku-20240307",
            temperature=0.1,
            max_tokens=4096,
            api_key_env_var="ANTHROPIC_API_KEY"
        ),
        LLMProvider.MOCK: LLMConfig(
            provider=LLMProvider.MOCK,
            model="mock-model",
            temperature=0.1,
            max_tokens=1000,
            api_key_env_var=""
        )
    }
    
    # Application Settings
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    DEBUG_MODE = os.getenv("DEBUG", "false").lower() == "true"
    
    # LLM Debug Settings
    LLM_DEBUG_ENABLED = os.getenv("LLM_DEBUG", "true").lower() == "true"
    LLM_REQUEST_LOGGING = os.getenv("LLM_REQUEST_LOGGING", "true").lower() == "true"
    LLM_RESPONSE_LOGGING = os.getenv("LLM_RESPONSE_LOGGING", "true").lower() == "true"
    
    # Provider Priority (fallback order)
    PROVIDER_PRIORITY = [
        LLMProvider.GEMINI,
        LLMProvider.OPENAI,
        LLMProvider.ANTHROPIC,
        LLMProvider.MOCK
    ]
    
    @classmethod
    def get_llm_config(cls, provider: LLMProvider) -> LLMConfig:
        """Get LLM configuration for provider"""
        return cls.LLM_CONFIGS.get(provider)
    
    @classmethod
    def get_default_provider(cls) -> LLMProvider:
        """Get default LLM provider based on availability"""
        for provider in cls.PROVIDER_PRIORITY:
            config = cls.get_llm_config(provider)
            if config and cls.is_provider_available(provider):
                return provider
        return LLMProvider.MOCK
    
    @classmethod
    def is_provider_available(cls, provider: LLMProvider) -> bool:
        """Check if provider is available and configured"""
        if provider == LLMProvider.MOCK:
            return True
            
        config = cls.get_llm_config(provider)
        if not config:
            return False
            
        # Check if API key is available
        if config.api_key_env_var:
            api_key = os.getenv(config.api_key_env_var) or os.getenv("GOOGLE_API_KEY")
            return bool(api_key)
            
        return True
    
    @classmethod
    def get_available_providers(cls) -> list[LLMProvider]:
        """Get list of available providers"""
        return [provider for provider in cls.PROVIDER_PRIORITY 
                if cls.is_provider_available(provider)]
    
    @classmethod
    def get_environment_info(cls) -> Dict[str, Any]:
        """Get environment configuration info"""
        return {
            "database_url": cls.DATABASE_URL,
            "log_level": cls.LOG_LEVEL,
            "debug_mode": cls.DEBUG_MODE,
            "llm_debug_enabled": cls.LLM_DEBUG_ENABLED,
            "default_provider": cls.get_default_provider().value,
            "available_providers": [p.value for p in cls.get_available_providers()],
            "environment_vars": {
                "GEMINI_API_KEY": bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")),
                "OPENAI_API_KEY": bool(os.getenv("OPENAI_API_KEY")),
                "ANTHROPIC_API_KEY": bool(os.getenv("ANTHROPIC_API_KEY")),
                "DATABASE_URL": bool(os.getenv("DATABASE_URL")),
            }
        }


# Export commonly used configurations for backward compatibility
DEFAULT_PROVIDER = Config.get_default_provider()
AVAILABLE_PROVIDERS = Config.get_available_providers()
LLM_DEBUG_ENABLED = Config.LLM_DEBUG_ENABLED
