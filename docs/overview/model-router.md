# Model Router Architecture - Hierarchical Routing System

## Executive Summary

This document outlines a sophisticated model routing system where:
- A **router model** intelligently directs queries to specialized models
- Routes to **categorized models** (Easy, Reasoning, Extreme/Advanced)
- Falls back only when the router model is **offline**
- Supports **dynamic model categorization** via SQLite configuration
- Provides a **settings UI** for model management

---

## Current Model Landscape

### Available Models & Initial Classification

| Model | Base Size | Category | Strengths | Use Cases |
|-------|-----------|----------|-----------|-----------|
| **qwen:4b** | 4B | Easy | Fast, general purpose | General Q&A, simple tasks |
| **qwen2.5-coder:7b** | 7B | Extreme | Code generation, debugging | Programming, technical tasks |
| **llama3.2:11b** | 11B | Reasoning | Strong reasoning, analysis | Complex analysis, reasoning |

---

## Architecture Overview

### System Flow Diagram

```
┌─────────────────────────────────────┐
│     USER INPUT / PROMPT             │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│  CHECK ROUTER MODEL STATUS                              │
│  - Is router model online?                              │
│  - Fallback enabled?                                    │
└────────────┬──────────────────────────┬────────────────┘
             │                          │
          YES│                          │NO
             │                          │
             ▼                          ▼
    ┌────────────────────┐    ┌──────────────────┐
    │ ROUTE VIA          │    │ USE FALLBACK     │
    │ ROUTER MODEL       │    │ STRATEGY         │
    │ (qwen:4b)          │    │ • Keyword router │
    │                    │    │ • Default model  │
    │ Input:             │    │ • Error to user  │
    │ • Prompt           │    └──────────────────┘
    │ • Model categories │
    │ • Available models │
    │                    │
    │ Output:            │
    │ {                  │
    │  model: "name",    │
    │  category: "type", │
    │  reasoning: "..."  │
    │ }                  │
    └─────────┬──────────┘
              │
              ▼
    ┌────────────────────────────┐
    │ SEND TO SELECTED MODEL     │
    │ (Ollama)                   │
    └──────────────┬─────────────┘
                   │
                   ▼
    ┌────────────────────────────┐
    │ STREAM RESPONSE TO USER    │
    │ (with routing metadata)    │
    └────────────────────────────┘
```

---

## Core Components

### 1. Model Router Engine

**Responsibility**: Analyze prompts and route to best model

```python
class IntelligentModelRouter:
    def __init__(self, router_model: str = "qwen:4b"):
        self.router_model = router_model  # Router model name
        self.ollama_client = OllamaClient()
        self.keyword_router = ModelRouter()  # Fallback
        
    async def route(self, prompt: str, models_config: Dict) -> RoutingDecision:
        """
        Main routing method.
        
        Args:
            prompt: User input
            models_config: Dict of available models + their categories
            
        Returns:
            RoutingDecision with selected model and reasoning
        """
        # Check if router model is available
        if not await self._is_model_online(self.router_model):
            return await self._fallback_route(prompt, models_config)
        
        # Call router model with structured prompt
        decision = await self._call_router_model(prompt, models_config)
        return decision
    
    async def _call_router_model(self, prompt: str, models_config: Dict) -> RoutingDecision:
        """
        Query the router model with a structured prompt.
        """
        # Create router prompt with model categories
        router_prompt = self._build_router_prompt(prompt, models_config)
        
        # Get response from router model
        response = await self.ollama_client.chat_stream(
            model=self.router_model,
            messages=[{"role": "user", "content": router_prompt}]
        )
        
        # Parse routing decision from response
        decision = self._parse_routing_decision(response)
        return decision
    
    async def _fallback_route(self, prompt: str, models_config: Dict) -> RoutingDecision:
        """
        Fallback routing when router model is offline.
        
        Strategy:
        1. Use keyword-based router
        2. Use model category recommendations
        3. Default to easiest/fastest model
        """
        fallback_model = self.keyword_router.route(prompt)
        return RoutingDecision(
            model=fallback_model,
            category=models_config[fallback_model]["category"],
            reasoning="Router model offline - using keyword fallback",
            is_fallback=True
        )
```

### 2. Model Category System

**Key Insight**: Models are categorized by complexity level, not task type

```python
class ModelCategory(Enum):
    """Model capability categories"""
    EASY = "easy"           # Fast, general purpose (4-5B params)
    REASONING = "reasoning" # Strong reasoning (7-13B params)
    EXTREME = "extreme"     # Powerful, slow (13B+ params)
    CUSTOM = "custom"       # User-defined categories
```

### 3. Router Prompt Design

The router model receives a structured prompt like:

```
You are an intelligent model router. Your job is to analyze queries and route them to the most appropriate model.

Available Models:
1. qwen:4b (Category: easy, Strength: general purpose, speed)
2. qwen2.5-coder:7b (Category: extreme, Strength: code generation, debugging)
3. llama3.2:11b (Category: reasoning, Strength: analysis, complex reasoning)

Query: "Debug this Python function that's returning None"

Your response MUST be valid JSON in this format:
{
  "model": "model_name",
  "category": "category_name",
  "reasoning": "Why this model is best for this query",
  "alternatives": [
    {"model": "model_name", "score": 0.8}
  ]
}

Query: [USER_INPUT_HERE]

Respond with ONLY the JSON, no additional text.
```

### 4. Routing Decision Object

```python
class RoutingDecision:
    model: str                           # Selected model name
    category: str                        # Model category
    reasoning: str                       # Why this model was chosen
    alternatives: List[Dict]             # Alternative models with scores
    is_fallback: bool = False            # Was fallback used?
    confidence: Optional[float] = None   # How confident (0-1)
    metadata: Dict = {}                  # Additional info
```

---

## Database Schema

### New Table: `model_categories`

Stores the categorization of all available models.

```sql
CREATE TABLE IF NOT EXISTS model_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name TEXT UNIQUE NOT NULL,           -- e.g., "qwen:4b"
    category TEXT NOT NULL,                    -- "easy", "reasoning", "extreme", "custom"
    display_name TEXT,                         -- Friendly name
    description TEXT,                          -- Model description
    strengths TEXT,                            -- JSON array of strengths
    parameters TEXT,                           -- Model size info
    is_active BOOLEAN DEFAULT 1,               -- Is model available?
    custom_category_label TEXT,                -- For custom categories
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

### Updated Table: `settings`

Add router configuration:

```json
{
  "enable_router": true,
  "router_model": "qwen:4b",
  "fallback_strategy": "keyword_router",      // "keyword_router", "default_model", "error"
  "default_fallback_model": "qwen:4b",
  "router_timeout_ms": 3000,
  "enable_fallback": true
}
```

### Table: `routing_history` (Optional - for analytics)

Track routing decisions for debugging/improvement:

```sql
CREATE TABLE IF NOT EXISTS routing_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt TEXT,
    selected_model TEXT,
    category TEXT,
    is_fallback BOOLEAN,
    reasoning TEXT,
    created_at TEXT NOT NULL
);
```

---

## Settings UI Configuration

### Settings Panel Structure

```
┌─────────────────────────────────────────────────────────┐
│  ROUTER CONFIGURATION                                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ✓ Enable Router                    [Toggle]           │
│  Router Model: qwen:4b              [Dropdown]         │
│  Fallback Strategy: keyword_router  [Dropdown]         │
│  Default Fallback Model: qwen:4b    [Dropdown]         │
│  Router Timeout (ms): 3000          [Input]            │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  MODEL CATEGORIZATION                                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─ EASY (Fast, General Purpose)                       │
│  │  ✓ qwen:4b (4B params)                              │
│  │    └ Edit | Remove | Set as default                │
│  │                                                     │
│  ├─ REASONING (Strong Analysis)                        │
│  │  ✓ llama3.2:11b (11B params)                        │
│  │    └ Edit | Remove | Set as default                │
│  │                                                     │
│  ├─ EXTREME (Advanced, Slow)                           │
│  │  ✓ qwen2.5-coder:7b (7B params)                     │
│  │    └ Edit | Remove | Set as default                │
│  │                                                     │
│  └─ CUSTOM CATEGORIES                                  │
│     [+ Add Category]                                   │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  NEW MODELS                                             │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Available from Ollama:                                │
│  • mistral:7b        [Assign Category ▼]  [Add]       │
│  • neural-chat:7b    [Assign Category ▼]  [Add]       │
│  • phi:2.7b          [Assign Category ▼]  [Add]       │
│                                                         │
│                      [Save] [Reset] [Advanced]         │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Data Flow with Model Categories

### Example 1: Coding Task

```
User: "Fix this JavaScript bug: [code snippet]"
        ↓
Router Prompt:
"Available models:
- qwen:4b (easy): general purpose
- llama3.2:11b (reasoning): strong analysis
- qwen2.5-coder:7b (extreme): code/debugging

Query: Fix this JavaScript bug..."
        ↓
Router Response (qwen:4b):
{
  "model": "qwen2.5-coder:7b",
  "category": "extreme",
  "reasoning": "Detected code debugging task. qwen2.5-coder is specialized for this.",
  "alternatives": [
    {"model": "llama3.2:11b", "score": 0.6}
  ]
}
        ↓
Selected Model: qwen2.5-coder:7b
        ↓
Response streamed to user with metadata:
{
  "model": "qwen2.5-coder:7b",
  "category": "extreme",
  "routed_by": "qwen:4b",
  "routing_reasoning": "Code debugging - extreme category recommended"
}
```

### Example 2: Router Offline - Fallback

```
User: "What is machine learning?"
        ↓
Check Router Status: OFFLINE ❌
        ↓
Use Fallback Strategy: keyword_router
        ↓
Keyword Router → selects "qwen:4b" (easy category)
        ↓
Response to user:
{
  "model": "qwen:4b",
  "category": "easy",
  "note": "Router offline - using fallback routing",
  "is_fallback": true
}
```

---

## Implementation Flow

### Phase 1: Database & Configuration

1. **Add `model_categories` table** to SQLite
2. **Populate initial categories** with existing 3 models:
   - qwen:4b → easy
   - llama3.2:11b → reasoning
   - qwen2.5-coder:7b → extreme
3. **Update settings storage** for router config
4. **Create database utilities** for model category CRUD

### Phase 2: Router Engine

1. **Create `IntelligentModelRouter` class**
2. **Implement router prompt builder** with model metadata
3. **Implement fallback strategies**
4. **Add router status checking** (is model online?)
5. **Create routing decision parser**

### Phase 3: Backend Integration

1. **Update `/chat` endpoint** to use intelligent router
2. **Add `/router/config` endpoint** (get/update model categories)
3. **Add `/router/test` endpoint** (test routing decisions)
4. **Add `/router/status` endpoint** (check router model status)
5. **Update chat response metadata** with routing info

### Phase 4: Frontend UI

1. **Create Settings → Router Configuration panel**
2. **Model category management UI**
3. **New model detection & categorization**
4. **Display routing decisions in chat**
5. **Router status indicator**

---

## API Endpoints

### Get Router Configuration

```bash
GET /router/config

Response:
{
  "router_model": "qwen:4b",
  "enable_router": true,
  "fallback_strategy": "keyword_router",
  "models": {
    "qwen:4b": {
      "category": "easy",
      "display_name": "Qwen 4B",
      "strengths": ["fast", "general_purpose"],
      "is_active": true
    },
    "llama3.2:11b": {
      "category": "reasoning",
      "display_name": "Llama 3.2",
      "strengths": ["reasoning", "analysis"],
      "is_active": true
    }
  }
}
```

### Update Model Category

```bash
POST /router/config/models

Body:
{
  "model_name": "mistral:7b",
  "category": "reasoning",
  "display_name": "Mistral 7B",
  "strengths": ["code", "reasoning"]
}

Response: { "success": true, "model": {...} }
```

### Test Router Decision

```bash
POST /router/test

Body:
{
  "prompt": "Fix this Python bug: [code]"
}

Response:
{
  "model": "qwen2.5-coder:7b",
  "category": "extreme",
  "reasoning": "Code debugging detected...",
  "alternatives": [...]
}
```

### Get Router Status

```bash
GET /router/status

Response:
{
  "router_online": true,
  "router_model": "qwen:4b",
  "fallback_available": true,
  "available_models": 3,
  "response_time_ms": 245
}
```

---

## Model Category Guidelines

### EASY Category
- **Size**: 1B - 5B parameters
- **Speed**: Very fast (200-400ms first token)
- **Best for**: General Q&A, simple tasks, summaries
- **Examples**: qwen:4b, phi:2.7b
- **Strengths**:
  - Fast response time
  - Low memory usage
  - Good for real-time interaction

### REASONING Category
- **Size**: 7B - 13B parameters
- **Speed**: Moderate (400-800ms first token)
- **Best for**: Analysis, comparison, complex reasoning, writing
- **Examples**: llama3.2:11b, neural-chat:7b
- **Strengths**:
  - Strong analytical capability
  - Better context understanding
  - Good for nuanced responses

### EXTREME Category
- **Size**: 13B+ parameters
- **Speed**: Slower (1-3s first token)
- **Best for**: Code generation, debugging, specialized tasks
- **Examples**: qwen2.5-coder:7b, mistral:7b (if large)
- **Strengths**:
  - Specialized capabilities
  - Better code understanding
  - Superior performance on complex tasks

### CUSTOM Category
- User-defined categories
- Example: "specialized", "slow-accurate", "lightweight"
- Useful for organization and specific use cases

---

## Error Handling & Edge Cases

### Case 1: Router Model Offline
```
Action: Use fallback strategy immediately
Response includes: "Router offline - using fallback routing"
```

### Case 2: No Models in Requested Category
```
Router Request: Route to "extreme" model
Available: Only "easy" models online

Action: Use keyword router or default model
Return: Error indication + fallback selection
```

### Case 3: Malformed Router Response
```
Router returns invalid JSON

Action: 
1. Log error
2. Use keyword router fallback
3. Continue without breaking
```

### Case 4: Router Response Timeout
```
Router takes > 3000ms to respond

Action:
1. Cancel waiting
2. Use keyword router immediately
3. Log timeout for debugging
```

---

## Monitoring & Analytics

### Optional: Routing History Table

Track every routing decision for analysis:

```sql
CREATE TABLE IF NOT EXISTS routing_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt TEXT NOT NULL,
    prompt_length INTEGER,
    selected_model TEXT NOT NULL,
    category TEXT NOT NULL,
    is_fallback BOOLEAN,
    fallback_reason TEXT,
    reasoning TEXT,
    response_time_ms INTEGER,
    created_at TEXT NOT NULL
);
```

**Use cases**:
- Analyze routing patterns
- Detect router model issues
- Optimize router prompt
- Debug misrouting

---

## Configuration Examples

### Minimal Config (3 models)
```json
{
  "enable_router": true,
  "router_model": "qwen:4b",
  "fallback_strategy": "keyword_router",
  "models": {
    "qwen:4b": {"category": "easy"},
    "llama3.2:11b": {"category": "reasoning"},
    "qwen2.5-coder:7b": {"category": "extreme"}
  }
}
```

### Advanced Config (multiple categories)
```json
{
  "enable_router": true,
  "router_model": "qwen:4b",
  "fallback_strategy": "default_model",
  "default_fallback_model": "qwen:4b",
  "models": {
    "qwen:4b": {"category": "easy"},
    "llama3.2:11b": {"category": "reasoning"},
    "qwen2.5-coder:7b": {"category": "extreme"},
    "mistral:7b": {"category": "custom", "label": "multilingual"},
    "phi:2.7b": {"category": "easy", "label": "lightweight"}
  },
  "custom_categories": {
    "multilingual": {"strengths": ["translation", "multilingual"], "priority": 7},
    "lightweight": {"strengths": ["edge_devices", "speed"], "priority": 9}
  }
}
```

---

## Security & Privacy

- ✅ All routing happens locally
- ✅ No data sent to external services
- ✅ Model categories stored in SQLite
- ✅ Routing decisions logged locally
- ✅ User has full control over model assignments

---

## Future Enhancements

- [ ] Machine learning-based router optimization
- [ ] User feedback loop for routing accuracy
- [ ] A/B testing different router models
- [ ] Seasonal/contextual category adjustments
- [ ] Per-user model preferences
- [ ] Routing analytics dashboard
- [ ] Estimated response time based on category
- [ ] Model performance metrics tracking

---

## Summary

This hierarchical routing system provides:

1. **Intelligent Routing**: Router model handles all decisions
2. **Flexible Categories**: Organize models by capability level
3. **Easy Configuration**: UI-based model management
4. **Graceful Fallback**: Uses keyword routing when router offline
5. **Extensible**: Support for custom categories
6. **Local & Secure**: No external dependencies
7. **Transparent**: Routing decisions included in responses

The architecture is designed to be **robust**, **configurable**, and **efficient**, allowing the system to intelligently route queries without relying on brittle keyword matching while gracefully degrading when needed.
