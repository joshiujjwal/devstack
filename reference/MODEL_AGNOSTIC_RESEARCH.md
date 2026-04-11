# RESEARCH: Model-Agnostic Multi-Agent Systems
## Building True Zero-Code Model Switching Architecture

---

## EXECUTIVE SUMMARY

A truly model-agnostic system requires:
1. **Provider Adapter Layer**: Normalize between provider formats (done at adapter level)
2. **Capability Matrix**: Runtime discovery of model capabilities
3. **Provider-Neutral Prompts**: Templates that adapt per model
4. **Cost-Aware Routing**: Route by task complexity to appropriate tier
5. **Resilient Fallback**: Circuit breaker + fallback chains
6. **Config-Only Switching**: Zero code changes via YAML/JSON

**Key Finding**: LiteLLM's success comes from separating adapter logic from routing logic.
Portkey adds cost calculation and capability discovery. TinyFlow shows inheritance-based abstraction.

---

## 1. LITELLM ARCHITECTURE ANALYSIS

### How LiteLLM Abstracts Providers

**Pattern**: Single `completion()` function accepts model_name string
```python
response = litellm.completion(
    model="gpt-4o",  # Can swap to "claude-3-opus" or "gemini-2.0-pro"
    messages=[...],
)
```

**Under the hood**:
- Provider detection from model_name prefix (gpt-4 → openai, claude → anthropic)
- Provider-specific module imported dynamically
- Normalized input format → provider-specific format
- Provider response → normalized response

**Adapter Pattern** (in litellm/llms/):
```
litellm/llms/
├── openai.py          # OpenAI-specific logic
├── anthropic.py       # Anthropic-specific logic
├── gemini.py          # Google-specific logic
└── custom_llm.py      # Base class
```

### Capability Flags (Model Metadata)

LiteLLM maintains `model_cost.json` with metadata:
```json
{
  "gpt-4o": {
    "input_cost_per_token": 2.5e-6,
    "output_cost_per_token": 10e-6,
    "supports_function_calling": true,
    "supports_vision": true,
    "max_tokens": 128000,
    "context_window": 128000
  }
}
```

**Key insight**: Metadata is queried at runtime, enabling:
- New model detection (release new version → update metadata only)
- Capability-based routing
- Cost calculation before request

### Provider-Specific Quirks Handled

| Quirk | OpenAI | Anthropic | Gemini |
|-------|--------|-----------|--------|
| **System Message** | Anywhere in array | Must be FIRST message, separate `system=` param | Separate `system_instruction` param |
| **Tool Call Format** | JSON with `tool_calls[].function` | XML tags `<tool_use>` | JSON with nested `functionCall` |
| **Tool Choice** | Supports `tool_choice="required"` | Must use in prompt | Not supported directly |
| **Vision URL** | Supports direct URLs | Base64 only | Supports URLs |
| **Function Definition** | OpenAI schema | Anthropic schema | Different schema |

**LiteLLM's Solution**: Provider-specific conversion at adapter layer
```python
# In openai.py
messages = convert_to_openai_format(messages)
tools = convert_tools_to_openai_schema(tools)
response = await openai_client.chat.completions.create(...)

# In anthropic.py
system_message = extract_system_message(messages)  # Must be separate
messages = remove_system_messages(messages)
tools = convert_tools_to_anthropic_xml(tools)
response = await anthropic_client.messages.create(system=system_message, ...)
```

---

## 2. PROVIDER CAPABILITY MATRIX

### Comprehensive Capabilities Schema

```python
@dataclass
class ModelCapabilities:
    # Core LLM capabilities
    supports_function_calling: bool
    supports_vision: bool
    supports_system_message: bool
    supports_json_mode: bool
    supports_streaming: bool
    supports_structured_output: bool
    supports_tool_choice: bool
    supports_vision_url: bool
    supports_batch_processing: bool
    supports_reasoning: bool  # o1/DeepSeek-r1
    
    # Context
    context_window: int
    max_output_tokens: int
    
    # Cost
    input_cost_per_token: float
    output_cost_per_token: float
    
    # Provider quirks (from research)
    provider_quirks: Dict[str, Any]
```

### Runtime Capability Querying

**Problem**: Models update frequently. Can't hard-code capabilities.

**Solution**: Query registry at request time
```python
class CapabilityRegistry:
    def get_capabilities(self, model_id: str) -> ModelCapabilities:
        # 1. Check local cache
        if model_id in self.cache:
            caps = self.cache[model_id]
            if not self.is_stale(caps):
                return caps
        
        # 2. Query external registry (Portkey API / custom DB)
        caps = await self.query_external_registry(model_id)
        
        # 3. Cache locally
        self.cache[model_id] = caps
        
        return caps
```

### Capability-Based Routing

```python
class CapabilityBasedRouter:
    def select_model_for_task(self, requirements):
        """
        Returns: List of models supporting ALL requirements
        """
        required_caps = [
            ModelCapability.FUNCTION_CALLING,
            ModelCapability.VISION,
        ]
        
        candidates = []
        for model in self.all_models:
            caps = self.registry.get_capabilities(model)
            if all(getattr(caps, cap.value) for cap in required_caps):
                candidates.append(model)
        
        # Filter by cost/latency/availability
        return self.rank_by_cost(candidates)
```

---

## 3. PROMPT PORTABILITY PATTERNS

### The Core Problem

Claude and GPT respond differently to same prompt:
- Claude prefers **XML-like structure**
- GPT prefers **markdown headers**
- Gemini prefers **clear sections**

### Solution: Adapter-Based Prompt Rendering

```python
class PromptTemplate:
    def __init__(self, template: str):
        # Store neutral template with markers
        self.template = """You are a helpful assistant.
        
Key instruction: {instruction}
        
<important>Follow these rules:</important>
- Be accurate
- Show reasoning
"""
    
    def render(self, model_capabilities: ModelCapabilities, **vars):
        prompt = self.template
        
        # 1. Substitute variables
        for k, v in vars.items():
            prompt = prompt.replace(f"{{{k}}}", v)
        
        # 2. Adapt for provider
        provider = model_capabilities.provider
        
        if provider == "anthropic":
            # Claude: Keep XML-like format
            prompt = prompt.replace("<important>", "<important>")
        elif provider == "openai":
            # GPT: Convert to markdown
            prompt = prompt.replace("<important>", "**IMPORTANT:**")
        elif provider == "google":
            # Gemini: Use clear sections
            prompt = prompt.replace("<important>", "IMPORTANT:")
        
        return prompt
```

### Key Pattern: Provider-Neutral Prompts

**Rule 1**: Use language that works across all models
- ❌ "Use XML tags for structure" (Gemini doesn't prefer this)
- ✓ "Structure your response in clear sections"

**Rule 2**: Avoid provider-specific instructions
- ❌ "Use the tool_choice parameter to force tool calling"
- ✓ "Always use tools for external lookups"

**Rule 3**: Few-shot examples that work universally
```python
EXAMPLE = """
User: What's the capital of France?
Assistant: The capital of France is Paris. It's located on the Seine River.

User: Calculate 15 * 23
Assistant: I'll use a calculator tool for this.

[Tool call: multiply(15, 23)]
[Tool result: 345]

The answer is 345.
"""
```

### Prompt Adaptation by Model Family

**For Claude**:
- XML-style tags for structure
- Constitutional AI framing ("You should..." vs "You must...")
- Longer thinking sections work better

**For GPT**:
- Markdown headers for structure
- Clear imperative instructions
- Numbered lists preferred

**For Gemini**:
- Clean paragraph structure
- Explicit section breaks
- Technical clarity emphasized

---

## 4. MODEL CAPABILITY DISCOVERY

### Portkey.ai's Approach

Portkey maintains **global model registry** updated automatically:

```json
{
  "gpt-4o": {
    "provider": "openai",
    "latency_p50_ms": 245,
    "latency_p99_ms": 1250,
    "availability_percent": 99.9,
    "supports_vision": true,
    "context_window": 128000,
    "cost": {"input": 2.5e-6, "output": 10e-6}
  }
}
```

**Real-time Discovery**:
1. New model released (e.g., GPT-5)
2. Portkey detects in public API
3. Registry auto-updates
4. Your code automatically routes to it (no code change)

### Implementation Pattern

```python
class AutoDiscoveryRegistry:
    def __init__(self, refresh_interval_hours=24):
        self.registry = {}
        self.refresh_interval = refresh_interval_hours
        self.last_refresh = None
    
    async def refresh_models(self):
        """Check for new models from each provider API."""
        
        # Call provider list_models() endpoints
        openai_models = await self.openai_client.models.list()
        anthropic_models = await self.anthropic_client.models.list()
        gemini_models = await self.gemini_client.models.list()
        
        # Merge with local metadata
        for model in openai_models:
            caps = ModelCapabilities(
                model_id=model.id,
                provider="openai",
                supports_function_calling=True,  # OpenAI supports this
                context_window=self._extract_context_window(model),
                # ... populate all fields
            )
            self.registry[model.id] = caps
        
        self.last_refresh = datetime.utcnow()
    
    async def get_capabilities(self, model_id: str):
        # Auto-refresh if stale
        if self._is_stale():
            await self.refresh_models()
        
        return self.registry.get(model_id)
```

---

## 5. FALLBACK & CIRCUIT-BREAKER PATTERNS

### Circuit Breaker State Machine

```
CLOSED (normal) 
  → [failure threshold reached] 
→ OPEN (failing, reject requests)
  → [timeout expired]
→ HALF_OPEN (testing recovery)
  → [success threshold reached]
→ CLOSED
  → [failures resume]
→ OPEN
```

### Implementation in Production

```python
class ResilientRouter:
    async def call_with_fallback(self, chain: FallbackChain, messages):
        """
        chain.models = ["gpt-4o", "claude-3-opus", "gemini-2.0-pro"]
        
        Tries in order, falling back if model fails.
        """
        
        for model_id in chain.models:
            breaker = self.breakers[model_id]
            
            # Check circuit state
            if breaker.state == CircuitBreakerState.OPEN:
                logging.info(f"Skip {model_id}: circuit is OPEN")
                continue
            
            try:
                # Try to call model
                response = await breaker.call(
                    self.call_model,
                    model_id=model_id,
                    messages=messages,
                )
                return response
            
            except RateLimitError:
                # Expected: Claude hit rate limit
                logging.warning(f"{model_id} rate limited, trying next")
                continue
            
            except APIConnectionError as e:
                # Unexpected: Mark for circuit breaker
                logging.error(f"{model_id} API error: {e}")
                breaker.record_failure()
                if breaker.is_open():
                    logging.critical(f"Circuit breaker opened for {model_id}")
                continue
        
        # All failed: queue for retry with exponential backoff
        await self.retry_queue.put({
            "chain_id": chain.id,
            "messages": messages,
            "retry_count": 0,
            "next_retry_secs": 60,
        })
        
        return None
```

### State Management for Queued Tasks

**Problem**: If all models fail, task is queued. Need to preserve state.

**Solution**: Use persistent queue (Redis/PostgreSQL)

```python
class PersistentRetryQueue:
    async def enqueue_retry(self, task):
        """Persist to Redis for durability."""
        task_id = hashlib.sha256(str(task).encode()).hexdigest()
        
        await self.redis.setex(
            f"retry:{task_id}",
            key_value={
                "chain_id": task["chain_id"],
                "messages": json.dumps(task["messages"]),
                "retry_count": task["retry_count"],
                "created_at": datetime.utcnow().isoformat(),
            },
            timeout=86400 * 7,  # 7 days
        )
    
    async def process_queued_tasks(self):
        """Background worker: retry failed tasks."""
        while True:
            # Get next queued task
            task = await self.redis.lpop("retry_queue")
            
            if not task:
                await asyncio.sleep(60)  # Check every minute
                continue
            
            task = json.loads(task)
            
            # Retry with exponential backoff
            if task["retry_count"] < 5:
                try:
                    response = await self.call_with_fallback(
                        chain_id=task["chain_id"],
                        messages=json.loads(task["messages"]),
                    )
                    
                    # Success: process response
                    await self.handle_response(response)
                
                except Exception:
                    task["retry_count"] += 1
                    task["next_retry_secs"] *= 2  # Exponential backoff
                    await asyncio.sleep(task["next_retry_secs"])
                    await self.enqueue_retry(task)  # Re-queue
```

---

## 6. COST-AWARE ROUTING

### Task Complexity Mapping

| Complexity | Task | Ideal Model | Cost |
|-----------|------|------------|------|
| **TRIVIAL** | Tokenize, count | gpt-4o-mini | $0.00015/1k |
| **SIMPLE** | Q&A, summarize | gpt-4o-mini | $0.00015/1k |
| **MODERATE** | Analysis, extraction | gpt-4o | $2.5/1M |
| **COMPLEX** | Code gen, reasoning | claude-3-opus | $15/1M |
| **EXPERT** | Novel problem solving | gpt-4-turbo | $10/1M |

### Routing Algorithm

```python
class CostAwareRouter:
    def select_model(self, task_complexity, required_capabilities=None):
        """
        Select cheapest model supporting task.
        
        Algorithm:
        1. Find tier for complexity level
        2. Filter by required capabilities
        3. Filter by cost budget
        4. Select model with lowest hourly cost
        """
        
        # 1. Get tier
        tier = self.tiers[task_complexity]
        candidates = tier.models
        
        # 2. Filter capabilities
        if required_capabilities:
            candidates = [
                m for m in candidates
                if self._has_capabilities(m, required_capabilities)
            ]
        
        # 3. Filter cost
        daily_budget = 100.0
        estimated_tokens = self._estimate_tokens(task_complexity)
        max_cost = daily_budget / 1000  # Distribute across requests
        
        candidates = [
            m for m in candidates
            if self._estimate_cost(m, estimated_tokens) < max_cost
        ]
        
        # 4. Return cheapest
        if candidates:
            return min(
                candidates,
                key=lambda m: self._hourly_cost(m),
            )
        
        return None
```

### Cost Calculation Pattern

```python
def calculate_request_cost(self, model_id, input_tokens, output_tokens):
    caps = self.registry.get_capabilities(model_id)
    
    input_cost = input_tokens * caps.input_cost_per_token
    output_cost = output_tokens * caps.output_cost_per_token
    
    total = input_cost + output_cost
    
    # Log for analytics
    logging.info(f"Model {model_id}: {input_tokens} in, {output_tokens} out = ${total:.4f}")
    
    return total
```

---

## 7. COMPLETE ARCHITECTURE SUMMARY

### Data Flow

```
Agent Request
    ↓
CostAwareRouter.select_model() → gpt-4o
    ↓
ResilientRouter.call_with_fallback(
    chain=["gpt-4o", "claude-3-sonnet", "gemini-2"],
    messages=[...],
)
    ↓
ProviderAdapter[openai].normalize_messages()
    ↓
API Call (with Circuit Breaker)
    ↓
Response → ProviderAdapter.denormalize()
    ↓
Normalized Response
    ↓
Agent processes result
```

### Config-Only Switching

**Change this**:
```yaml
# config.yaml
agent:
  active_model_id: gpt-4o
  fallback_chain:
    - gpt-4o
    - claude-3-sonnet
    - gemini-2.0-pro
```

**To this**:
```yaml
agent:
  active_model_id: claude-3-opus  # ONE LINE CHANGE
  fallback_chain:
    - claude-3-opus
    - gpt-4-turbo
    - gemini-2.0-pro
```

**Zero code changes needed.**

---

## 8. KEY RESEARCH FINDINGS

### From LiteLLM
- ✓ Single unified interface via provider detection
- ✓ 100+ providers supported
- ✓ Metadata registry for capabilities
- ✓ Provider-specific adapters handle quirks

### From Portkey
- ✓ Global model registry with auto-discovery
- ✓ Capability-based routing engine
- ✓ Cost tracking and budget enforcement
- ✓ Circuit breaker per model

### From TinyFlow
- ✓ Clean abstract base class (BaseLLM)
- ✓ Provider-specific subclasses (AnthropicProvider, OpenAIProvider)
- ✓ Factory pattern for provider instantiation
- ✓ Message normalization at adapter level

### Critical Insights
1. **Separation of Concerns**: Routing logic ≠ Adapter logic
2. **Provider Quirks**: Handle at adapter layer, not in agent code
3. **Capability Discovery**: Query at runtime, not hard-coded
4. **Prompt Adaptability**: Same semantic meaning, different syntax per provider
5. **Resilience**: Circuit breaker + fallback chains required for production

---

## 9. PRODUCTION CHECKLIST

- [ ] Provider adapters for all used models
- [ ] Capability matrix with all models and metadata
- [ ] Provider-neutral prompt templates with model-specific rendering
- [ ] Cost-aware router with task complexity mapping
- [ ] Circuit breaker for each model
- [ ] Fallback chains defined in config
- [ ] Persistent retry queue (Redis/DB)
- [ ] Config file (YAML/JSON) for model switching
- [ ] Monitoring: latency, cost, error rate per model
- [ ] Automated capability discovery (refresh weekly)
- [ ] Load testing with model failover scenarios

