"""
MODEL-AGNOSTIC MULTI-AGENT ARCHITECTURE
========================================

Comprehensive research and implementation for zero-code model switching.

Research Findings:
1. LiteLLM: 100+ provider abstraction via provider-specific adapters
2. Portkey: Model routing with capability-based selection
3. TinyFlow: Base class inheritance for provider neutrality
4. Key insight: Separate data normalization from provider adapters
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, AsyncGenerator, Union
import json
import logging
import asyncio

# ============================================================================
# 1. PROVIDER CAPABILITY MATRIX - Runtime capability discovery
# ============================================================================

class ModelCapability(str, Enum):
    FUNCTION_CALLING = "supports_function_calling"
    VISION = "supports_vision"
    SYSTEM_MESSAGE = "supports_system_message"
    JSON_MODE = "supports_json_mode"
    STREAMING = "supports_streaming"
    STRUCTURED_OUTPUT = "supports_structured_output"
    TOOL_CHOICE = "supports_tool_choice"
    VISION_URL = "supports_vision_url"
    REASONING = "supports_reasoning"

@dataclass
class ModelCapabilities:
    """Runtime capability matrix for a model - queried before every request."""
    model_id: str
    provider: str
    
    # Core capabilities
    supports_function_calling: bool = False
    supports_vision: bool = False
    supports_system_message: bool = True
    supports_json_mode: bool = False
    supports_streaming: bool = True
    supports_structured_output: bool = False
    supports_tool_choice: bool = False
    supports_vision_url: bool = False
    supports_reasoning: bool = False
    
    # Context windows and pricing
    context_window: int = 4096
    max_output_tokens: int = 2048
    input_cost_per_token: float = 0.0
    output_cost_per_token: float = 0.0
    
    # Provider-specific quirks
    provider_quirks: Dict[str, Any] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.utcnow)

@dataclass
class ProviderCapabilityMatrix:
    """Registry mapping model_id -> capabilities."""
    models: Dict[str, ModelCapabilities] = field(default_factory=dict)
    
    def get_capabilities(self, model_id: str) -> Optional[ModelCapabilities]:
        return self.models.get(model_id)
    
    def filter_by_capability(self, capability: ModelCapability) -> List[ModelCapabilities]:
        """Find all models supporting a specific capability."""
        return [cap for cap in self.models.values() if getattr(cap, capability.value, False)]

# ============================================================================
# 2. PROVIDER-AGNOSTIC MESSAGE FORMAT
# ============================================================================

class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"

@dataclass
class Message:
    """Provider-agnostic message - normalized across all providers."""
    role: MessageRole
    content: str
    tool_calls: Optional[List] = None
    tool_call_id: Optional[str] = None
    reasoning_content: Optional[str] = None

# ============================================================================
# 3. PROVIDER ADAPTER LAYER - Transforms between normalized and provider format
# ============================================================================

class ProviderAdapter(ABC):
    """Transforms between provider-neutral and provider-specific formats."""
    
    def __init__(self, capabilities: ModelCapabilities):
        self.capabilities = capabilities
    
    @abstractmethod
    def normalize_messages(self, messages: List[Message]) -> Any:
        """Convert to provider format."""
        pass
    
    @abstractmethod
    def denormalize_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Convert provider response to normalized format."""
        pass

class AnthropicAdapter(ProviderAdapter):
    """
    KEY QUIRK: Anthropic requires system message as FIRST message, 
    not in message array. Must be passed separately.
    """
    
    def normalize_messages(self, messages: List[Message]):
        system_prompt = ""
        claude_messages = []
        
        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                system_prompt += msg.content
            else:
                claude_messages.append({"role": msg.role.value, "content": msg.content})
        
        return {"messages": claude_messages, "system": system_prompt}
    
    def denormalize_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        content = ""
        tool_calls = []
        
        for block in response.get("content", []):
            if block.get("type") == "text":
                content += block.get("text", "")
            elif block.get("type") == "tool_use":
                tool_calls.append({
                    "id": block["id"],
                    "name": block["name"],
                    "arguments": block["input"],
                })
        
        return {"content": content, "tool_calls": tool_calls}

class OpenAIAdapter(ProviderAdapter):
    """OpenAI/GPT accepts system message anywhere in array."""
    
    def normalize_messages(self, messages: List[Message]):
        openai_messages = []
        for msg in messages:
            openai_msg = {"role": msg.role.value, "content": msg.content}
            openai_messages.append(openai_msg)
        return {"messages": openai_messages}
    
    def denormalize_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        choice = response.get("choices", [{}])[0]
        message = choice.get("message", {})
        
        return {
            "content": message.get("content", ""),
            "tool_calls": message.get("tool_calls", []),
        }

class GeminiAdapter(ProviderAdapter):
    """
    KEY QUIRK: Gemini's system message goes in separate 'system_instruction' param,
    not in messages. Also uses different role names: 'user' vs 'model'.
    """
    
    def normalize_messages(self, messages: List[Message]):
        system_instruction = ""
        gemini_messages = []
        
        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                system_instruction += msg.content
            else:
                role = "user" if msg.role == MessageRole.USER else "model"
                gemini_messages.append({"role": role, "parts": [{"text": msg.content}]})
        
        return {"messages": gemini_messages, "system_instruction": system_instruction}
    
    def denormalize_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        content = ""
        tool_calls = []
        
        for candidate in response.get("candidates", []):
            for part in candidate.get("content", {}).get("parts", []):
                if "text" in part:
                    content += part["text"]
                elif "functionCall" in part:
                    fc = part["functionCall"]
                    tool_calls.append({
                        "id": fc.get("id", ""),
                        "name": fc.get("name", ""),
                        "arguments": fc.get("args", {}),
                    })
        
        return {"content": content, "tool_calls": tool_calls}

# ============================================================================
# 4. PROVIDER-NEUTRAL PROMPTS (Critical for true model agnosticism)
# ============================================================================

class PromptTemplate:
    """
    Provider-neutral prompts that adapt for each model.
    Key principle: Same semantic meaning across all models.
    """
    
    def __init__(self, template: str):
        self.template = template
    
    def render(self, capabilities: ModelCapabilities, **variables) -> str:
        """Render prompt, adapting for model if needed."""
        prompt = self.template
        
        # Variable substitution
        for key, value in variables.items():
            prompt = prompt.replace(f"{{{key}}}", str(value))
        
        # Model-specific adaptation
        provider = capabilities.provider
        if provider == "anthropic":
            prompt = prompt.replace("<important>", "⚠️ Important: ")
        elif provider == "openai":
            prompt = prompt.replace("<important>", "**IMPORTANT:**\n")
        elif provider == "google":
            prompt = prompt.replace("<important>", "IMPORTANT:\n")
        
        return prompt

SYSTEM_PROMPT_REASONING = PromptTemplate("""You are an expert problem-solver.

Approach:
1. Understand the problem deeply
2. Break it into steps  
3. Verify each step
4. State conclusion clearly

<important>Show your reasoning, not just answers.</important>
""")

# ============================================================================
# 5. COST-AWARE TASK ROUTING
# ============================================================================

class TaskComplexity(str, Enum):
    TRIVIAL = "trivial"
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    EXPERT = "expert"

@dataclass
class ModelTier:
    tier_name: str
    models: List[str]
    cost_budget: float
    use_cases: List[TaskComplexity] = field(default_factory=list)

class CostAwareRouter:
    """Route tasks to appropriate model tier based on complexity and cost."""
    
    def __init__(self, capability_matrix: ProviderCapabilityMatrix):
        self.capability_matrix = capability_matrix
        self.tiers = {
            "ultra_cheap": ModelTier(
                tier_name="ultra_cheap",
                models=["gpt-4o-mini", "claude-3-haiku"],
                cost_budget=0.0001,
                use_cases=[TaskComplexity.TRIVIAL, TaskComplexity.SIMPLE]
            ),
            "budget": ModelTier(
                tier_name="budget",
                models=["gpt-4o", "claude-3-sonnet"],
                cost_budget=0.001,
                use_cases=[TaskComplexity.SIMPLE, TaskComplexity.MODERATE]
            ),
            "premium": ModelTier(
                tier_name="premium",
                models=["gpt-4-turbo", "claude-3-opus"],
                cost_budget=0.01,
                use_cases=[TaskComplexity.COMPLEX, TaskComplexity.EXPERT]
            ),
        }
    
    def select_model(
        self,
        task_complexity: TaskComplexity,
        required_capabilities: List[ModelCapability] = None,
    ) -> Optional[str]:
        """Select cheapest model supporting task."""
        
        for tier in self.tiers.values():
            if task_complexity not in tier.use_cases:
                continue
            
            # Filter by capabilities
            candidates = []
            for model_id in tier.models:
                caps = self.capability_matrix.get_capabilities(model_id)
                if caps:
                    if not required_capabilities or all(
                        getattr(caps, cap.value, False) for cap in required_capabilities
                    ):
                        candidates.append(model_id)
            
            # Return cheapest
            if candidates:
                return min(
                    candidates,
                    key=lambda m: self.capability_matrix.get_capabilities(m).input_cost_per_token
                )
        
        return None

# ============================================================================
# 6. CIRCUIT BREAKER & FALLBACK PATTERNS
# ============================================================================

class CircuitBreakerState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    """Prevent cascading failures via circuit breaker pattern."""
    
    def __init__(self, model_id: str, failure_threshold: int = 5, recovery_timeout_secs: int = 60):
        self.model_id = model_id
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout_secs = recovery_timeout_secs
        self.opened_at = None
    
    async def call(self, fn: Callable, *args, **kwargs) -> Any:
        """Execute with circuit breaker protection."""
        
        if self.state == CircuitBreakerState.OPEN:
            if (datetime.utcnow() - self.opened_at).seconds > self.recovery_timeout_secs:
                self.state = CircuitBreakerState.HALF_OPEN
            else:
                raise Exception(f"Circuit breaker OPEN for {self.model_id}")
        
        try:
            result = await fn(*args, **kwargs)
            self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitBreakerState.OPEN
                self.opened_at = datetime.utcnow()
                logging.warning(f"Circuit breaker OPEN for {self.model_id}")
            raise

class ResilientModelRouter:
    """Router with fallback chain and circuit breaker support."""
    
    def __init__(self, capability_matrix: ProviderCapabilityMatrix):
        self.capability_matrix = capability_matrix
        self.fallback_chains: Dict[str, List[str]] = {}
        self.breakers: Dict[str, CircuitBreaker] = {}
        self.retry_queue = asyncio.Queue()
    
    def register_fallback_chain(self, chain_id: str, models: List[str]):
        """Register fallback chain: [primary, secondary, tertiary]."""
        self.fallback_chains[chain_id] = models
        for model in models:
            if model not in self.breakers:
                self.breakers[model] = CircuitBreaker(model)
    
    async def call_with_fallback(
        self,
        chain_id: str,
        messages: List[Message],
        **call_kwargs,
    ) -> Optional[Dict[str, Any]]:
        """Call model with automatic fallback chain."""
        
        models = self.fallback_chains.get(chain_id, [])
        last_error = None
        
        for model_id in models:
            breaker = self.breakers[model_id]
            
            if breaker.state == CircuitBreakerState.OPEN:
                logging.warning(f"Skipping {model_id}, circuit breaker OPEN")
                continue
            
            try:
                adapter = self._get_adapter(model_id)
                result = await breaker.call(adapter.call, messages=messages, **call_kwargs)
                logging.info(f"Successfully called {model_id}")
                return result
            except Exception as e:
                last_error = e
                logging.error(f"Model {model_id} failed: {e}")
                continue
        
        logging.error(f"All models in chain {chain_id} failed.")
        await self.retry_queue.put({"chain_id": chain_id, "messages": messages, "error": str(last_error)})
        return None
    
    def _get_adapter(self, model_id: str) -> ProviderAdapter:
        """Get provider adapter for model."""
        caps = self.capability_matrix.get_capabilities(model_id)
        
        if caps.provider == "openai":
            return OpenAIAdapter(caps)
        elif caps.provider == "anthropic":
            return AnthropicAdapter(caps)
        elif caps.provider == "google":
            return GeminiAdapter(caps)
        else:
            raise ValueError(f"Unknown provider for {model_id}")

# ============================================================================
# 7. AGENT CONFIG SCHEMA - Zero code changes for model switching
# ============================================================================

@dataclass
class ModelConfig:
    model_id: str
    provider: str
    api_key_env_var: str
    tier: str
    enabled: bool = True

@dataclass
class AgentConfig:
    """Complete agent configuration for model-agnostic switching."""
    active_model_id: str
    models: Dict[str, ModelConfig] = field(default_factory=dict)
    fallback_chains: Dict[str, List[str]] = field(default_factory=dict)
    routing_strategy: str = "cost_aware"
    max_cost_per_request: Optional[float] = 0.01
    system_prompt: PromptTemplate = SYSTEM_PROMPT_REASONING
    task_complexity_to_model: Dict[TaskComplexity, str] = field(default_factory=dict)

# ============================================================================
# 8. COMPLETE MODEL REGISTRY with all major models
# ============================================================================

MODEL_REGISTRY = {
    "gpt-4o": {
        "provider": "openai",
        "supports_function_calling": True,
        "supports_vision": True,
        "supports_json_mode": True,
        "supports_structured_output": True,
        "supports_tool_choice": True,
        "supports_vision_url": True,
        "context_window": 128000,
        "max_output_tokens": 4096,
        "input_cost_per_token": 2.5e-6,
        "output_cost_per_token": 10e-6,
    },
    "claude-3-5-sonnet-20241022": {
        "provider": "anthropic",
        "supports_function_calling": True,
        "supports_vision": True,
        "supports_json_mode": False,
        "supports_structured_output": True,
        "supports_tool_choice": True,
        "supports_vision_url": False,
        "context_window": 200000,
        "max_output_tokens": 4096,
        "input_cost_per_token": 3e-6,
        "output_cost_per_token": 15e-6,
    },
    "gemini-2.0-pro": {
        "provider": "google",
        "supports_function_calling": True,
        "supports_vision": True,
        "supports_json_mode": False,
        "supports_structured_output": True,
        "supports_tool_choice": False,
        "supports_vision_url": True,
        "context_window": 1000000,
        "max_output_tokens": 8192,
        "input_cost_per_token": 0.075e-6,
        "output_cost_per_token": 0.3e-6,
    },
}

print("Model-agnostic architecture module loaded successfully.")
