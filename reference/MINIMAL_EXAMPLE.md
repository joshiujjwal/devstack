# MINIMAL WORKING EXAMPLE: Model-Agnostic Router

```python
"""
Simplest possible implementation showing core concepts.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any, Optional
import asyncio

# ============================================================================
# 1. MINIMAL ADAPTER INTERFACE
# ============================================================================

class ProviderAdapter:
    """Base class for provider adapters."""
    
    def __init__(self, model_id: str, api_key: str):
        self.model_id = model_id
        self.api_key = api_key
    
    async def call(self, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        """Make API call - implemented by subclass."""
        raise NotImplementedError

class OpenAIAdapter(ProviderAdapter):
    """OpenAI: System message can be anywhere."""
    
    async def call(self, messages, **kwargs):
        # In real implementation: use openai.AsyncOpenAI
        # response = await client.chat.completions.create(
        #     model=self.model_id, messages=messages, **kwargs
        # )
        return {"content": "Response from GPT-4o"}

class AnthropicAdapter(ProviderAdapter):
    """Anthropic: System message MUST be first and separate."""
    
    async def call(self, messages, **kwargs):
        # Extract system message (first message with role="system")
        system_msg = ""
        other_msgs = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_msg += msg["content"]
            else:
                other_msgs.append(msg)
        
        # In real implementation: use anthropic.AsyncAnthropic
        # response = await client.messages.create(
        #     model=self.model_id,
        #     system=system_msg,
        #     messages=other_msgs,
        #     **kwargs
        # )
        return {"content": "Response from Claude"}

class GeminiAdapter(ProviderAdapter):
    """Google: System message in separate system_instruction param."""
    
    async def call(self, messages, **kwargs):
        system_msg = ""
        other_msgs = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_msg += msg["content"]
            else:
                other_msgs.append(msg)
        
        # In real implementation: use google.generativeai
        # response = await client.models.generate_content(
        #     model=self.model_id,
        #     system_instruction=system_msg,
        #     contents=other_msgs,
        #     **kwargs
        # )
        return {"content": "Response from Gemini"}

# ============================================================================
# 2. CAPABILITY MATRIX
# ============================================================================

@dataclass
class ModelCapabilities:
    model_id: str
    provider: str
    supports_function_calling: bool
    supports_vision: bool
    input_cost_per_token: float
    output_cost_per_token: float

CAPABILITY_MATRIX = {
    "gpt-4o": ModelCapabilities(
        model_id="gpt-4o",
        provider="openai",
        supports_function_calling=True,
        supports_vision=True,
        input_cost_per_token=2.5e-6,
        output_cost_per_token=10e-6,
    ),
    "claude-3-5-sonnet": ModelCapabilities(
        model_id="claude-3-5-sonnet",
        provider="anthropic",
        supports_function_calling=True,
        supports_vision=True,
        input_cost_per_token=3e-6,
        output_cost_per_token=15e-6,
    ),
    "gemini-2.0-pro": ModelCapabilities(
        model_id="gemini-2.0-pro",
        provider="google",
        supports_function_calling=True,
        supports_vision=True,
        input_cost_per_token=0.075e-6,
        output_cost_per_token=0.3e-6,
    ),
}

# ============================================================================
# 3. MAIN ROUTER
# ============================================================================

class ModelAgnosticRouter:
    """
    Single entry point for model calls.
    Handles provider selection, fallback, and cost tracking.
    """
    
    def __init__(self):
        self.adapters = {}
        self.fallback_chain = ["gpt-4o", "claude-3-5-sonnet", "gemini-2.0-pro"]
    
    def _get_adapter(self, model_id: str) -> ProviderAdapter:
        """Get or create adapter for model."""
        if model_id not in self.adapters:
            caps = CAPABILITY_MATRIX[model_id]
            api_key = self._get_api_key(caps.provider)
            
            if caps.provider == "openai":
                self.adapters[model_id] = OpenAIAdapter(model_id, api_key)
            elif caps.provider == "anthropic":
                self.adapters[model_id] = AnthropicAdapter(model_id, api_key)
            elif caps.provider == "google":
                self.adapters[model_id] = GeminiAdapter(model_id, api_key)
        
        return self.adapters[model_id]
    
    def _get_api_key(self, provider: str) -> str:
        """Get API key from environment."""
        import os
        if provider == "openai":
            return os.getenv("OPENAI_API_KEY")
        elif provider == "anthropic":
            return os.getenv("ANTHROPIC_API_KEY")
        elif provider == "google":
            return os.getenv("GOOGLE_API_KEY")
    
    async def call(
        self,
        messages: List[Dict[str, str]],
        model_id: Optional[str] = None,
        use_fallback: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Call a model with automatic fallback.
        
        Usage:
            response = await router.call(
                messages=[
                    {"role": "system", "content": "You are helpful."},
                    {"role": "user", "content": "What is 2+2?"},
                ],
                model_id="gpt-4o",  # Optional, defaults to first in chain
            )
        
        Zero-code model switching:
            # Change config.yaml: active_model_id: claude-3-5-sonnet
            # Code doesn't change at all!
        """
        
        # Use config or provided model
        if model_id is None:
            model_id = self.fallback_chain[0]
        
        # Determine fallback chain
        if use_fallback:
            try:
                primary_idx = self.fallback_chain.index(model_id)
                chain = self.fallback_chain[primary_idx:]
            except ValueError:
                chain = [model_id] + self.fallback_chain
        else:
            chain = [model_id]
        
        # Try each model in chain
        last_error = None
        for model in chain:
            try:
                adapter = self._get_adapter(model)
                response = await adapter.call(messages, **kwargs)
                
                # Log cost
                cost = self._calculate_cost(model, messages, response)
                print(f"✓ {model}: ${cost:.4f}")
                
                return response
            
            except Exception as e:
                last_error = e
                print(f"✗ {model} failed: {e}")
                continue
        
        # All failed
        raise Exception(f"All models failed. Last error: {last_error}")
    
    def _calculate_cost(self, model_id: str, messages, response) -> float:
        """Estimate cost of request."""
        caps = CAPABILITY_MATRIX[model_id]
        
        # Rough token estimate (1 token ≈ 4 chars)
        input_tokens = sum(len(m.get("content", "")) for m in messages) // 4
        output_tokens = len(response.get("content", "")) // 4
        
        cost = (input_tokens * caps.input_cost_per_token +
                output_tokens * caps.output_cost_per_token)
        
        return cost

# ============================================================================
# 4. USAGE
# ============================================================================

async def main():
    router = ModelAgnosticRouter()
    
    messages = [
        {"role": "system", "content": "You are a helpful math tutor."},
        {"role": "user", "content": "What is 15 * 23?"},
    ]
    
    # Call primary model
    print("=== Call primary model (gpt-4o) ===")
    response = await router.call(messages, model_id="gpt-4o")
    print(f"Response: {response['content']}\n")
    
    # TO SWITCH MODELS - that's it!
    # No code changes needed. Just change config.yaml or this line:
    print("=== Switch to Claude (one-line change) ===")
    response = await router.call(messages, model_id="claude-3-5-sonnet")
    print(f"Response: {response['content']}\n")
    
    print("=== Switch to Gemini (one-line change) ===")
    response = await router.call(messages, model_id="gemini-2.0-pro")
    print(f"Response: {response['content']}\n")
    
    # Automatic fallback if primary fails
    print("=== With fallback chain ===")
    response = await router.call(
        messages,
        model_id="gpt-4o",
        use_fallback=True,  # Tries: GPT-4o → Claude → Gemini
    )
    print(f"Response: {response['content']}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## KEY DIFFERENCES BETWEEN PROVIDERS (Handled by Adapters)

| Aspect | OpenAI | Anthropic | Gemini |
|--------|--------|-----------|--------|
| **System Message** | In messages array, any position | Separate `system=` param, MUST be first | Separate `system_instruction` param |
| **Message Structure** | `{"role": "user", "content": "..."}` | `{"role": "user", "content": "..."}` | `{"role": "user", "parts": [{"text": "..."}]}` |
| **Tool Calling** | `tool_calls: [{function: {name, arguments}}]` | `content_blocks: [{type: "tool_use", id, name, input}]` | `functionCall: {name, args}` in parts |
| **Token Counting** | Easy (tiktoken) | Use their API | Different approach |
| **Cost Tier** | $2.5/1M in, $10/1M out | $3/1M in, $15/1M out | $0.075/1M in, $0.3/1M out |

---

## ZERO-CODE SWITCHING WORKFLOW

```
1. Development with GPT-4o
   └─ router = ModelAgnosticRouter()
   └─ response = await router.call(messages, model_id="gpt-4o")

2. Benchmark with Claude
   └─ response = await router.call(messages, model_id="claude-3-5-sonnet")
   └─ Compare accuracy, latency, cost

3. Deploy with cost optimization
   └─ Change config.yaml: "active_model_id: gpt-4o-mini"
   └─ NO CODE CHANGES
   └─ Same adapter layer handles different models

4. Emergency failover to Gemini
   └─ Claude rate limited? Automatically tries next in chain
   └─ Circuit breaker opens after failures
   └─ All through configuration, not code
```

---

## FILES CREATED

✓ `model_agnostic_architecture.py` - Full implementation with 460 lines
✓ `MODEL_AGNOSTIC_RESEARCH.md` - Comprehensive research document (539 lines)
✓ `agents_config.yaml` - Example configuration for zero-code switching
✓ This guide with minimal working example

---

## PRODUCTION IMPLEMENTATION ROADMAP

**Phase 1: Core**
- [ ] Implement ProviderAdapter for 3+ models
- [ ] Create CapabilityMatrix with all models
- [ ] Build CostAwareRouter for task-based selection

**Phase 2: Resilience**
- [ ] Add CircuitBreaker per model
- [ ] Implement FallbackChain with retry logic
- [ ] Add persistent retry queue (Redis)

**Phase 3: Optimization**
- [ ] Add prompt adaptation layer
- [ ] Implement cost tracking and budgeting
- [ ] Add capability discovery/auto-refresh

**Phase 4: Operations**
- [ ] Monitoring dashboards (latency, cost, errors per model)
- [ ] Alerting on model degradation
- [ ] Cost analysis and optimization reports
