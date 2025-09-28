"""
Multi-provider LLM Service for supporting different AI providers.
Supports OpenAI, Anthropic, Google, and other providers.
"""

import json
import logging
import time
from typing import Dict, Any, Optional, List, Union
from enum import Enum
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class LLMProvider(Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    GITHUB_COPILOT = "github_copilot"

@dataclass
class LLMConfig:
    """Configuration for LLM provider."""
    provider: LLMProvider
    model: str
    api_key: str
    base_url: Optional[str] = None
    temperature: float = 0.1
    max_tokens: Optional[int] = None

@dataclass
class LLMResponse:
    """Standardized LLM response."""
    content: str
    raw_response: Dict[str, Any]
    provider: LLMProvider
    model: str
    latency_ms: int
    usage: Optional[Dict[str, int]] = None

class LLMService:
    """Multi-provider LLM service."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.debug_logger = logging.getLogger("llm_debug")
        self._clients = {}
        self._load_configurations()
    
    def _load_configurations(self):
        """Load LLM configurations from environment variables."""
        self.configs = {}
        
        # OpenAI Configuration
        if os.getenv("OPENAI_API_KEY"):
            self.configs[LLMProvider.OPENAI] = LLMConfig(
                provider=LLMProvider.OPENAI,
                model=os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview"),
                api_key=os.getenv("OPENAI_API_KEY"),
                base_url=os.getenv("OPENAI_BASE_URL"),
                temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.1")),
                max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "4000")) if os.getenv("OPENAI_MAX_TOKENS") else None
            )
        
        # Anthropic Configuration
        if os.getenv("ANTHROPIC_API_KEY"):
            self.configs[LLMProvider.ANTHROPIC] = LLMConfig(
                provider=LLMProvider.ANTHROPIC,
                model=os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229"),
                api_key=os.getenv("ANTHROPIC_API_KEY"),
                temperature=float(os.getenv("ANTHROPIC_TEMPERATURE", "0.1")),
                max_tokens=int(os.getenv("ANTHROPIC_MAX_TOKENS", "4000")) if os.getenv("ANTHROPIC_MAX_TOKENS") else None
            )
        
        # Gemini Configuration
        if os.getenv("GOOGLE_API_KEY"):
            self.configs[LLMProvider.GEMINI] = LLMConfig(
                provider=LLMProvider.GEMINI,
                model=os.getenv("GEMINI_MODEL", "models/gemini-pro-latest"),
                api_key=os.getenv("GOOGLE_API_KEY"),
                temperature=float(os.getenv("GEMINI_TEMPERATURE", "0.1")),
                max_tokens=int(os.getenv("GEMINI_MAX_TOKENS", "4000")) if os.getenv("GEMINI_MAX_TOKENS") else None
            )
        
        # Default provider
        self.default_provider = LLMProvider(os.getenv("DEFAULT_LLM_PROVIDER", "gemini"))
        if self.default_provider not in self.configs:
            available = list(self.configs.keys())
            if available:
                self.default_provider = available[0]
            else:
                raise ValueError("No LLM providers configured! Set API keys in environment variables.")
    
    def _get_client(self, provider: LLMProvider):
        """Get or create client for the specified provider."""
        if provider in self._clients:
            return self._clients[provider]
        
        config = self.configs.get(provider)
        if not config:
            raise ValueError(f"Provider {provider.value} not configured")
        
        if provider == LLMProvider.OPENAI:
            from openai import OpenAI
            client = OpenAI(
                api_key=config.api_key,
                base_url=config.base_url
            )
        elif provider == LLMProvider.ANTHROPIC:
            import anthropic
            client = anthropic.Anthropic(api_key=config.api_key)
        elif provider == LLMProvider.GEMINI:
            import google.generativeai as genai
            genai.configure(api_key=config.api_key)
            client = genai
        else:
            raise ValueError(f"Unsupported provider: {provider.value}")
        
        self._clients[provider] = client
        return client
    
    def _log_request(self, request_id: str, provider: LLMProvider, config: LLMConfig, prompt: str, files: Optional[List] = None, metadata: Optional[Dict] = None):
        """Log LLM request details."""
        self.debug_logger.info(f"🚀 LLM REQUEST [{request_id}]")
        self.debug_logger.info(f"  Provider: {provider.value}")
        self.debug_logger.info(f"  Model: {config.model}")
        self.debug_logger.info(f"  Temperature: {config.temperature}")
        self.debug_logger.info(f"  Max Tokens: {config.max_tokens}")
        
        if files:
            self.debug_logger.info(f"  Files: {len(files)} file(s)")
            for i, file_path in enumerate(files, 1):
                self.debug_logger.info(f"    File {i}: {file_path}")
        
        self.debug_logger.debug(f"  User Prompt: \n{prompt}")
        
        if metadata:
            self.debug_logger.debug(f"  Metadata: {json.dumps(metadata, indent=2)}")
    
    def _log_response(self, request_id: str, response: LLMResponse, success: bool = True):
        """Log LLM response details."""
        status = "✅ SUCCESS" if success else "❌ ERROR"
        self.debug_logger.info(f"{status} LLM RESPONSE [{request_id}]")
        self.debug_logger.info(f"  Provider: {response.provider.value}")
        self.debug_logger.info(f"  Model: {response.model}")
        self.debug_logger.info(f"  Latency: {response.latency_ms}ms")
        
        if response.usage:
            self.debug_logger.info(f"  Usage: {json.dumps(response.usage)}")
        
        self.debug_logger.debug(f"  Response: {response.content}")
        self.debug_logger.debug(f"  Raw Response: {json.dumps(response.raw_response, indent=2)}")
    
    def generate_text(self, 
                     prompt: str,
                     provider: Optional[LLMProvider] = None,
                     files: Optional[List[str]] = None,
                     metadata: Optional[Dict] = None) -> LLMResponse:
        """Generate text using specified or default LLM provider."""
        provider = provider or self.default_provider
        config = self.configs[provider]
        client = self._get_client(provider)
        
        # Generate unique request ID for tracking
        request_id = f"{provider.value}_{int(time.time() * 1000)}"
        
        # Log request
        self._log_request(request_id, provider, config, prompt, files, metadata)
        
        start_time = time.time()
        
        try:
            if provider == LLMProvider.OPENAI:
                response = self._call_openai(client, config, prompt, files)
            elif provider == LLMProvider.ANTHROPIC:
                response = self._call_anthropic(client, config, prompt, files)
            elif provider == LLMProvider.GEMINI:
                response = self._call_gemini(client, config, prompt, files)
            else:
                raise ValueError(f"Unsupported provider: {provider.value}")
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            llm_response = LLMResponse(
                content=response["content"],
                raw_response=response["raw"],
                provider=provider,
                model=config.model,
                latency_ms=latency_ms,
                usage=response.get("usage")
            )
            
            self._log_response(request_id, llm_response, success=True)
            return llm_response
            
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            error_response = LLMResponse(
                content="",
                raw_response={"error": str(e)},
                provider=provider,
                model=config.model,
                latency_ms=latency_ms
            )
            self._log_response(request_id, error_response, success=False)
            raise
    
    def _call_openai(self, client, config: LLMConfig, prompt: str, files: Optional[List[str]]) -> Dict:
        """Call OpenAI API."""
        messages = [{"role": "user", "content": prompt}]
        
        # Handle files if provided
        if files:
            # For multimodal, we'd need to encode images/documents
            self.logger.warning("File handling for OpenAI not yet implemented")
        
        response = client.chat.completions.create(
            model=config.model,
            messages=messages,
            temperature=config.temperature,
            max_tokens=config.max_tokens
        )
        
        return {
            "content": response.choices[0].message.content,
            "raw": response.model_dump(),
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }
    
    def _call_anthropic(self, client, config: LLMConfig, prompt: str, files: Optional[List[str]]) -> Dict:
        """Call Anthropic API."""
        if files:
            self.logger.warning("File handling for Anthropic not yet implemented")
        
        response = client.messages.create(
            model=config.model,
            max_tokens=config.max_tokens or 4000,
            temperature=config.temperature,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return {
            "content": response.content[0].text,
            "raw": response.model_dump(),
            "usage": {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens
            }
        }
    
    def _call_gemini(self, client, config: LLMConfig, prompt: str, files: Optional[List[str]]) -> Dict:
        """Call Gemini API."""
        model = client.GenerativeModel(config.model)
        
        # Prepare content
        content = [prompt]
        if files:
            for file_path in files:
                if file_path.lower().endswith('.pdf'):
                    uploaded_file = client.upload_file(file_path)
                    content.append(uploaded_file)
        
        generation_config = client.types.GenerationConfig(
            temperature=config.temperature,
            max_output_tokens=config.max_tokens
        )
        
        response = model.generate_content(
            content,
            generation_config=generation_config
        )
        
        usage = {}
        if hasattr(response, 'usage_metadata'):
            usage = {
                "prompt_tokens": response.usage_metadata.prompt_token_count,
                "completion_tokens": response.usage_metadata.candidates_token_count,
                "total_tokens": response.usage_metadata.total_token_count
            }
        
        return {
            "content": response.text,
            "raw": {"candidates": [{"content": response.text}]},
            "usage": usage
        }
    
    def list_available_providers(self) -> List[LLMProvider]:
        """Get list of configured providers."""
        return list(self.configs.keys())
    
    def get_default_provider(self) -> LLMProvider:
        """Get the default provider."""
        return self.default_provider
    
    def set_default_provider(self, provider: LLMProvider):
        """Set the default provider."""
        if provider not in self.configs:
            raise ValueError(f"Provider {provider.value} not configured")
        self.default_provider = provider


# Global instance
llm_service = LLMService()