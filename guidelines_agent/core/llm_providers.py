"""
Multi-vendor LLM Provider Abstraction Layer
============================================

Supports multiple LLM providers (Gemini, OpenAI, Anthropic, etc.) with:
- Unified interface for all providers
- Comprehensive debug logging
- Request/response tracking
- Error handling and fallback mechanisms
- Configuration management
"""

import os
import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

# Provider-specific imports (lazy loaded)
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class LLMProvider(Enum):
    """Supported LLM providers"""
    GEMINI = "gemini"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    MOCK = "mock"  # For development/testing


@dataclass
class LLMRequest:
    """Structured LLM request data"""
    prompt: str
    model: str
    provider: LLMProvider
    temperature: float = 0.1
    max_tokens: Optional[int] = None
    files: Optional[List[str]] = None  # File paths for multimodal
    system_prompt: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class LLMResponse:
    """Structured LLM response data"""
    content: str
    provider: LLMProvider
    model: str
    usage: Optional[Dict[str, int]] = None
    latency_ms: int = 0
    success: bool = True
    error: Optional[str] = None
    request_id: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None


class LLMDebugLogger:
    """Enhanced debugging logger for LLM requests/responses"""
    
    def __init__(self, logger_name: str = "llm_debug"):
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.DEBUG)
        
        # Create debug-specific formatter
        formatter = logging.Formatter(
            '%(asctime)s - LLM_DEBUG - %(levelname)s - %(message)s'
        )
        
        # Ensure we have a handler
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def log_request(self, request: LLMRequest, request_id: str):
        """Log LLM request details"""
        self.logger.info(f"🚀 LLM REQUEST [{request_id}]")
        self.logger.info(f"  Provider: {request.provider.value}")
        self.logger.info(f"  Model: {request.model}")
        self.logger.info(f"  Temperature: {request.temperature}")
        self.logger.info(f"  Max Tokens: {request.max_tokens}")
        
        if request.files:
            self.logger.info(f"  Files: {len(request.files)} file(s)")
            for i, file in enumerate(request.files):
                self.logger.info(f"    File {i+1}: {file}")
        
        if request.system_prompt:
            self.logger.debug(f"  System Prompt: {request.system_prompt[:200]}...")
        
        self.logger.debug(f"  User Prompt: {request.prompt[:500]}...")
        
        if request.metadata:
            self.logger.debug(f"  Metadata: {json.dumps(request.metadata, indent=2)}")
    
    def log_response(self, response: LLMResponse, request_id: str):
        """Log LLM response details"""
        status = "✅ SUCCESS" if response.success else "❌ FAILED"
        self.logger.info(f"{status} LLM RESPONSE [{request_id}]")
        self.logger.info(f"  Provider: {response.provider.value}")
        self.logger.info(f"  Model: {response.model}")
        self.logger.info(f"  Latency: {response.latency_ms}ms")
        
        if response.usage:
            self.logger.info(f"  Usage: {json.dumps(response.usage)}")
        
        if response.error:
            self.logger.error(f"  Error: {response.error}")
        else:
            response_preview = response.content[:300] + "..." if len(response.content) > 300 else response.content
            self.logger.debug(f"  Response: {response_preview}")
        
        if response.raw_response:
            self.logger.debug(f"  Raw Response: {json.dumps(response.raw_response, indent=2, default=str)}")


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    def __init__(self, debug_logger: LLMDebugLogger):
        self.debug_logger = debug_logger
    
    @abstractmethod
    def generate_response(self, request: LLMRequest) -> LLMResponse:
        """Generate response from LLM provider"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available and configured"""
        pass


class GeminiProvider(BaseLLMProvider):
    """Google Gemini LLM Provider"""
    
    def __init__(self, debug_logger: LLMDebugLogger):
        super().__init__(debug_logger)
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
    
    def is_available(self) -> bool:
        return GEMINI_AVAILABLE and bool(self.api_key)
    
    def generate_response(self, request: LLMRequest) -> LLMResponse:
        start_time = time.time()
        request_id = f"gemini_{int(start_time * 1000)}"
        
        try:
            self.debug_logger.log_request(request, request_id)
            
            model = genai.GenerativeModel(request.model)
            
            # Prepare content
            contents = [request.prompt]
            
            # Handle file uploads for multimodal
            if request.files:
                for file_path in request.files:
                    if os.path.exists(file_path):
                        mime_type = "application/pdf" if file_path.endswith('.pdf') else "auto"
                        uploaded_file = genai.upload_file(path=file_path, mime_type=mime_type)
                        contents.append(uploaded_file)
            
            # Generate response
            response = model.generate_content(
                contents,
                generation_config=genai.types.GenerationConfig(
                    temperature=request.temperature,
                    max_output_tokens=request.max_tokens
                )
            )
            
            end_time = time.time()
            latency_ms = int((end_time - start_time) * 1000)
            
            # Extract usage if available
            usage = None
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                usage = {
                    "prompt_tokens": getattr(response.usage_metadata, 'prompt_token_count', 0),
                    "completion_tokens": getattr(response.usage_metadata, 'candidates_token_count', 0),
                    "total_tokens": getattr(response.usage_metadata, 'total_token_count', 0)
                }
            
            llm_response = LLMResponse(
                content=response.text.strip(),
                provider=LLMProvider.GEMINI,
                model=request.model,
                usage=usage,
                latency_ms=latency_ms,
                success=True,
                request_id=request_id,
                raw_response={"candidates": [{"content": response.text}]}
            )
            
            self.debug_logger.log_response(llm_response, request_id)
            return llm_response
            
        except Exception as e:
            end_time = time.time()
            latency_ms = int((end_time - start_time) * 1000)
            
            error_response = LLMResponse(
                content="",
                provider=LLMProvider.GEMINI,
                model=request.model,
                latency_ms=latency_ms,
                success=False,
                error=str(e),
                request_id=request_id
            )
            
            self.debug_logger.log_response(error_response, request_id)
            return error_response


class OpenAIProvider(BaseLLMProvider):
    """OpenAI LLM Provider"""
    
    def __init__(self, debug_logger: LLMDebugLogger):
        super().__init__(debug_logger)
        self.api_key = os.getenv("OPENAI_API_KEY")
        if self.api_key:
            openai.api_key = self.api_key
    
    def is_available(self) -> bool:
        return OPENAI_AVAILABLE and bool(self.api_key)
    
    def generate_response(self, request: LLMRequest) -> LLMResponse:
        start_time = time.time()
        request_id = f"openai_{int(start_time * 1000)}"
        
        try:
            self.debug_logger.log_request(request, request_id)
            
            # Prepare messages
            messages = []
            if request.system_prompt:
                messages.append({"role": "system", "content": request.system_prompt})
            messages.append({"role": "user", "content": request.prompt})
            
            # Make API call
            response = openai.ChatCompletion.create(
                model=request.model,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
            
            end_time = time.time()
            latency_ms = int((end_time - start_time) * 1000)
            
            content = response.choices[0].message.content.strip()
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            
            llm_response = LLMResponse(
                content=content,
                provider=LLMProvider.OPENAI,
                model=request.model,
                usage=usage,
                latency_ms=latency_ms,
                success=True,
                request_id=request_id,
                raw_response=response.to_dict()
            )
            
            self.debug_logger.log_response(llm_response, request_id)
            return llm_response
            
        except Exception as e:
            end_time = time.time()
            latency_ms = int((end_time - start_time) * 1000)
            
            error_response = LLMResponse(
                content="",
                provider=LLMProvider.OPENAI,
                model=request.model,
                latency_ms=latency_ms,
                success=False,
                error=str(e),
                request_id=request_id
            )
            
            self.debug_logger.log_response(error_response, request_id)
            return error_response


class MockProvider(BaseLLMProvider):
    """Mock LLM Provider for development/testing"""
    
    def __init__(self, debug_logger: LLMDebugLogger):
        super().__init__(debug_logger)
    
    def is_available(self) -> bool:
        return True
    
    def generate_response(self, request: LLMRequest) -> LLMResponse:
        start_time = time.time()
        request_id = f"mock_{int(start_time * 1000)}"
        
        self.debug_logger.log_request(request, request_id)
        
        # Simulate processing time
        time.sleep(0.1)
        
        # Generate mock response based on prompt content
        if "extract" in request.prompt.lower() or "guidelines" in request.prompt.lower():
            mock_content = '''
{
  "is_valid_document": true,
  "validation_summary": "Mock: Valid investment guidelines document detected",
  "portfolio_id": "mock_portfolio_001",
  "portfolio_name": "Mock Test Portfolio",
  "doc_id": "mock_doc_123",
  "guidelines": [
    {
      "rule_id": "MOCK_001",
      "rule_text": "Mock guideline: Maximum 60% equity allocation",
      "category": "Asset Allocation"
    }
  ]
}
            '''.strip()
        elif "plan" in request.prompt.lower() or "query" in request.prompt.lower():
            mock_content = '''
{
  "search_query": "mock search terms",
  "summary_instruction": "Provide mock summary of guidelines",
  "top_k": 5
}
            '''.strip()
        else:
            mock_content = "Mock LLM response: This is a simulated response for development/testing purposes."
        
        end_time = time.time()
        latency_ms = int((end_time - start_time) * 1000)
        
        llm_response = LLMResponse(
            content=mock_content,
            provider=LLMProvider.MOCK,
            model=request.model,
            usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            latency_ms=latency_ms,
            success=True,
            request_id=request_id
        )
        
        self.debug_logger.log_response(llm_response, request_id)
        return llm_response


class LLMManager:
    """Main LLM Manager with multi-provider support and fallback logic"""
    
    def __init__(self):
        self.debug_logger = LLMDebugLogger()
        self.providers = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize available providers"""
        self.providers[LLMProvider.GEMINI] = GeminiProvider(self.debug_logger)
        self.providers[LLMProvider.OPENAI] = OpenAIProvider(self.debug_logger)
        self.providers[LLMProvider.MOCK] = MockProvider(self.debug_logger)
    
    def get_available_providers(self) -> List[LLMProvider]:
        """Get list of available and configured providers"""
        return [provider for provider, impl in self.providers.items() 
                if impl.is_available()]
    
    def get_default_provider(self) -> LLMProvider:
        """Get the default provider based on availability and configuration"""
        # Priority order: Gemini -> OpenAI -> Mock
        priority_order = [LLMProvider.GEMINI, LLMProvider.OPENAI, LLMProvider.MOCK]
        
        for provider in priority_order:
            if provider in self.providers and self.providers[provider].is_available():
                return provider
        
        # Fallback to mock if nothing else is available
        return LLMProvider.MOCK
    
    def generate_response(self, 
                         prompt: str,
                         model: Optional[str] = None,
                         provider: Optional[LLMProvider] = None,
                         temperature: float = 0.1,
                         max_tokens: Optional[int] = None,
                         files: Optional[List[str]] = None,
                         system_prompt: Optional[str] = None,
                         metadata: Optional[Dict[str, Any]] = None) -> LLMResponse:
        """
        Generate response using specified or default provider
        """
        # Use default provider if not specified
        if provider is None:
            provider = self.get_default_provider()
        
        # Set default model based on provider
        if model is None:
            model_defaults = {
                LLMProvider.GEMINI: "gemini-1.5-flash",
                LLMProvider.OPENAI: "gpt-3.5-turbo",
                LLMProvider.MOCK: "mock-model"
            }
            model = model_defaults.get(provider, "default-model")
        
        # Create request
        request = LLMRequest(
            prompt=prompt,
            model=model,
            provider=provider,
            temperature=temperature,
            max_tokens=max_tokens,
            files=files,
            system_prompt=system_prompt,
            metadata=metadata
        )
        
        # Get provider implementation
        provider_impl = self.providers.get(provider)
        if not provider_impl:
            raise ValueError(f"Provider {provider} not available")
        
        if not provider_impl.is_available():
            # Try fallback to available provider
            fallback_provider = self.get_default_provider()
            if fallback_provider != provider:
                self.debug_logger.logger.warning(
                    f"Provider {provider} not available, falling back to {fallback_provider}"
                )
                request.provider = fallback_provider
                provider_impl = self.providers[fallback_provider]
            else:
                raise ValueError(f"No available LLM providers configured")
        
        # Generate response
        return provider_impl.generate_response(request)


# Global LLM manager instance
llm_manager = LLMManager()


# Convenience functions for backward compatibility
def generate_llm_response(prompt: str, 
                         model: Optional[str] = None,
                         provider: Optional[LLMProvider] = None,
                         **kwargs) -> str:
    """Generate LLM response and return content only (backward compatibility)"""
    response = llm_manager.generate_response(prompt, model, provider, **kwargs)
    if not response.success:
        raise Exception(f"LLM generation failed: {response.error}")
    return response.content


def extract_with_llm(prompt: str, 
                    files: Optional[List[str]] = None, 
                    **kwargs) -> str:
    """Extract content using LLM with file support"""
    return generate_llm_response(prompt, files=files, **kwargs)