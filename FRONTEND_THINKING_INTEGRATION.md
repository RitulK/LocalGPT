# Frontend Integration: Thinking/Reasoning Toggle

## What to Add to Frontend

### 1. Update Settings Panel (Frontend/src/components/SettingsPanel.jsx)

Add thinking toggle to the settings:

```jsx
// Add to your settings state
const [enableThinking, setEnableThinking] = useState(false);
const [reasoningBudget, setReasoningBudget] = useState(8192);

// Add UI elements
<div className="setting">
  <label>Enable Extended Thinking (Nemotron only)</label>
  <input 
    type="checkbox" 
    checked={enableThinking}
    onChange={(e) => setEnableThinking(e.target.checked)}
  />
  <small>Model will reason before answering complex questions</small>
</div>

<div className="setting">
  <label>Reasoning Budget (tokens)</label>
  <select value={reasoningBudget} onChange={(e) => setReasoningBudget(Number(e.target.value))}>
    <option value={4096}>4096 (Quick)</option>
    <option value={8192}>8192 (Default)</option>
    <option value={16384}>16384 (Deep)</option>
  </select>
</div>
```

### 2. Update Chat Window (Frontend/src/components/ChatWindow.jsx)

Pass thinking settings to chat request:

```jsx
const handleSendMessage = async () => {
  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      prompt: message,
      model: selectedModel,
      enable_thinking: enableThinking,           // Add this
      reasoning_budget: reasoningBudget,         // Add this
      use_router: useRouter,
      conversation_id: currentConversation?.id,
    })
  });
  
  // Handle streaming responses
  const reader = response.body.getReader();
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    const text = new TextDecoder().decode(value);
    const lines = text.split('\n');
    
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        
        // Handle reasoning
        if (data.type === 'reasoning') {
          addReasoningBubble(data.content);
        }
        // Handle content
        else if (data.type === 'content') {
          appendMessage(data.content);
        }
      }
    }
  }
};
```

### 3. Display Reasoning (Optional)

Create a component to show reasoning in a collapsible box:

```jsx
// ReasoningBubble.jsx
export const ReasoningBubble = ({ content }) => {
  const [expanded, setExpanded] = useState(false);
  
  return (
    <div className="reasoning-bubble">
      <button onClick={() => setExpanded(!expanded)}>
        {expanded ? '▼ Thinking Process' : '▶ Show Thinking'}
      </button>
      {expanded && (
        <div className="reasoning-content">
          <p>{content}</p>
        </div>
      )}
    </div>
  );
};
```

### 4. CSS for Thinking UI

```css
.reasoning-bubble {
  background-color: #f0f4f8;
  border-left: 4px solid #6b7280;
  padding: 12px;
  margin: 8px 0;
  border-radius: 4px;
  font-size: 14px;
}

.reasoning-bubble button {
  background: none;
  border: none;
  cursor: pointer;
  color: #6b7280;
  font-weight: 500;
}

.reasoning-content {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #d1d5db;
  color: #6b7280;
}
```

### 5. Update Model Selector

Show when thinking is available:

```jsx
// In model dropdown
{models.map(model => (
  <option key={model.name} value={model.name}>
    {model.name}
    {model.name.includes('nemotron') && ' (with thinking)'}
  </option>
))}
```

## User Experience Flow

1. **User selects Nemotron model** → Thinking toggle becomes visible
2. **User enables thinking** → Sets reasoning budget if needed
3. **User sends message**
4. **Backend streams reasoning** (if enabled) → Shows in collapsible bubble
5. **Backend streams response** → Shows normal message
6. **User sees both thinking process and final answer**

## API Response Format

```json
// Metadata (first message)
{
  "type": "metadata",
  "model": "nvidia/nemotron-3-ultra-550b-a55b",
  "thinking_enabled": true
}

// Reasoning (if enabled)
{
  "type": "reasoning",
  "content": "Let me analyze this step by step...\n1. First, I need to understand...\n2. Then consider..."
}

// Final response
{
  "type": "content",
  "content": "Based on my analysis, here's my answer..."
}
```

## Testing

### Test 1: Thinking Disabled
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Why is the sky blue?",
    "model": "nvidia/nemotron-3-ultra-550b-a55b",
    "enable_thinking": false
  }'
```

### Test 2: Thinking Enabled
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain quantum entanglement",
    "model": "nvidia/nemotron-3-ultra-550b-a55b",
    "enable_thinking": true,
    "reasoning_budget": 8192
  }'
```

## Notes
- Thinking is only available for Nemotron models
- Disabling thinking on other models has no effect
- Reasoning takes time - responses will be slower
- Great for complex problems, not needed for simple questions
