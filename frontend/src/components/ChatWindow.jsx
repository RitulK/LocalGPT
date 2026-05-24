import { useState, useRef, useEffect } from 'react';
import MessageBubble from './MessageBubble';
import Aurora from './Aurora';
import { Send, Trash2, AlertCircle } from 'lucide-react';

export default function ChatWindow({
  conversation,
  onAddMessage,
  onUpdateLastMessage,
  onClearChat,
  selectedModel,
  useRouter,
  models,
  onSelectModel,
  onToggleRouter,
  apiUrl
}) {
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState('');
  const messagesEndRef = useRef(null);
  const messagesContainerRef = useRef(null);
  const textareaRef = useRef(null);

  const scrollToBottom = (smooth = false) => {
    // Use requestAnimationFrame to ensure scroll happens after DOM updates
    requestAnimationFrame(() => {
      if (messagesContainerRef.current) {
        if (smooth) {
          messagesContainerRef.current.scrollTo({
            top: messagesContainerRef.current.scrollHeight,
            behavior: 'smooth'
          });
        } else {
          messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight;
        }
      }
    });
  };

  useEffect(() => {
    // Smooth scroll when messages change but not streaming
    scrollToBottom(!isStreaming);
  }, [conversation?.messages]);

  // Instant scroll during streaming for better performance
  useEffect(() => {
    if (isStreaming) {
      scrollToBottom(false);
    }
  }, [isStreaming, conversation?.messages?.length, conversation?.messages?.[conversation?.messages?.length - 1]?.content]);

  useEffect(() => {
    // Auto-resize textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  }, [input]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;

    const userMessage = {
      role: 'user',
      content: input,
      timestamp: new Date()
    };

    // Prepare conversation history BEFORE adding new messages
    const history = conversation.messages.map(msg => ({
      role: msg.role,
      content: msg.content
    }));

    setInput('');
    setError('');
    onAddMessage(conversation.id, userMessage);

    // Create initial assistant message
    const assistantMessage = {
      role: 'assistant',
      content: '',
      model: selectedModel,
      timestamp: new Date(),
      isStreaming: true
    };
    onAddMessage(conversation.id, assistantMessage);

    setIsStreaming(true);

    try {
      const response = await fetch(`${apiUrl}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          prompt: input,
          model: useRouter ? null : selectedModel,
          use_router: useRouter,
          conversation_id: conversation.id,
          conversation_history: history
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let accumulatedContent = '';
      let actualModel = selectedModel;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              if (data.type === 'metadata') {
                actualModel = data.model;
                onUpdateLastMessage(conversation.id, { model: actualModel });
              } else if (data.type === 'content') {
                accumulatedContent += data.content;
                onUpdateLastMessage(conversation.id, { 
                  content: accumulatedContent,
                  model: actualModel
                });
              } else if (data.type === 'done') {
                onUpdateLastMessage(conversation.id, { 
                  isStreaming: false,
                  model: actualModel
                });
              }
            } catch (e) {
              console.error('Error parsing SSE:', e);
            }
          }
        }
      }
    } catch (err) {
      console.error('Chat error:', err);
      setError('Failed to get response from the model. Make sure Ollama is running.');
      onUpdateLastMessage(conversation.id, {
        content: '❌ Error: Failed to get response. Please check if Ollama is running.',
        isStreaming: false,
        error: true
      });
    } finally {
      setIsStreaming(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  if (!conversation) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center bg-gradient-to-br from-slate-950/50 to-slate-900/50">
        <div className="text-center px-6">
          <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-indigo-500/20 to-purple-600/20 flex items-center justify-center border border-indigo-500/30">
            <MessageBubble className="w-10 h-10 text-indigo-400" />
          </div>
          <h3 className="text-xl font-semibold text-slate-300 mb-2">No Conversation Selected</h3>
          <p className="text-slate-500 text-sm">Select or create a conversation to start chatting</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden bg-gradient-to-br from-slate-950/50 to-slate-900/50">
      {/* Messages Area */}
      <div ref={messagesContainerRef} className="flex-1 overflow-y-auto px-4 py-6 chat-scroll">
        {conversation.messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-slate-400 relative">
            {/* Aurora Background */}
            <div className="absolute inset-0">
              <Aurora
                colorStops={["#7cff67","#B19EEF","#5227FF"]}
                blend={0.5}
                amplitude={1.0}
                speed={1}
              />
            </div>

            {/* Content */}
            <div className="relative z-10 text-center">
              <h1 className="text-8xl font-bold mb-8 text-white drop-shadow-2xl">
                Hello
              </h1>
              <p className="text-xl text-white/90 max-w-2xl leading-relaxed drop-shadow-lg">
                Ask me anything! I'm powered by local LLMs running on your machine via Ollama.
              </p>
              {models.length === 0 && (
                <div className="mt-12 p-5 bg-amber-500/10 border border-amber-500/30 rounded-2xl max-w-md mx-auto backdrop-blur-md">
                  <div className="flex items-start gap-4">
                    <AlertCircle className="w-6 h-6 text-amber-400 flex-shrink-0 mt-1" />
                    <div className="text-sm">
                      <p className="font-semibold text-amber-300 mb-2 text-base">No models found</p>
                      <p className="text-slate-400 leading-relaxed">
                        Make sure Ollama is running and you have models installed.
                        Run: <code className="bg-slate-800/80 px-2 py-1 rounded-lg border border-slate-700/50 text-amber-400 font-mono text-xs">ollama pull llama3.2</code>
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="max-w-4xl mx-auto space-y-6">
            {conversation.messages.map((message, index) => (
              <MessageBubble 
                key={`${conversation.id}-${index}-${message.timestamp?.getTime() || index}`} 
                message={message} 
              />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div className="px-6 py-4 bg-red-500/5 border-t border-red-500/20 backdrop-blur-xl">
          <div className="max-w-4xl mx-auto flex items-center gap-3 text-red-400 text-sm">
            <div className="p-2 rounded-xl bg-red-500/10 backdrop-blur-sm border border-red-500/20">
              <AlertCircle className="w-5 h-5" />
            </div>
            <span className="font-medium">{error}</span>
          </div>
        </div>
      )}

      {/* Input Area */}
      <div className="border-t border-white/10 bg-slate-900/30 backdrop-blur-xl px-6 py-6 shadow-2xl">
        <div className="max-w-4xl mx-auto">
          <form onSubmit={handleSubmit} className="flex gap-3 items-end">
            {/* Model Selector Dropdown */}
            <div className="flex flex-col gap-2">
              <label className="text-xs font-medium text-slate-300">Model</label>
              <select
                value={selectedModel}
                onChange={(e) => {
                  const value = e.target.value;
                  onSelectModel(value);
                  onToggleRouter(value === 'auto');
                }}
                disabled={isStreaming}
                className="bg-white/10 text-slate-100 rounded-xl px-3 py-2 text-sm border border-white/20 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50 transition-all duration-300 backdrop-blur-md cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed shadow-lg"
                style={{
                  backdropFilter: 'blur(20px) saturate(180%)',
                  WebkitBackdropFilter: 'blur(20px) saturate(180%)',
                }}
              >
                <option value="auto">🤖 Auto</option>
                <option disabled>─────</option>
                {models.map((model) => (
                  <option key={model.name} value={model.name}>
                    {model.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex-1">
              <textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={`Ask anything${selectedModel !== 'auto' ? ` (${selectedModel})` : ''}...`}
                className="w-full bg-white/5 text-slate-100 placeholder-slate-400 rounded-2xl px-5 py-4 resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50 transition-all duration-300 max-h-40 border border-white/10 backdrop-blur-md shadow-lg"
                rows="1"
                disabled={isStreaming}
              />
            </div>
            <button
              type="submit"
              disabled={!input.trim() || isStreaming || models.length === 0}
              className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 disabled:from-slate-700 disabled:to-slate-700 disabled:cursor-not-allowed text-white rounded-2xl px-5 py-4 transition-all duration-300 flex items-center gap-2 font-medium shadow-lg shadow-indigo-500/30 hover:shadow-indigo-500/50 hover:scale-105 disabled:hover:scale-100 disabled:shadow-none backdrop-blur-sm"
            >
              <Send className="w-5 h-5" />
              {isStreaming ? 'Sending...' : 'Send'}
            </button>
            {conversation.messages.length > 0 && (
              <button
                type="button"
                onClick={onClearChat}
                disabled={isStreaming}
                className="bg-white/5 hover:bg-white/10 disabled:bg-white/5 disabled:cursor-not-allowed text-slate-300 hover:text-red-400 rounded-2xl px-5 py-4 transition-all duration-300 border border-white/10 hover:border-red-500/50 backdrop-blur-md"
                title="Clear chat"
              >
                <Trash2 className="w-5 h-5" />
              </button>
            )}
          </form>
          <div className="mt-3 text-xs text-slate-400 flex items-center justify-between">
            <span>
              Press <kbd className="px-2 py-0.5 bg-white/5 border border-white/10 rounded text-slate-300 backdrop-blur-sm">Enter</kbd> to send, <kbd className="px-2 py-0.5 bg-white/5 border border-white/10 rounded text-slate-300 backdrop-blur-sm">Shift + Enter</kbd> for new line
            </span>
            {useRouter && (
              <span className="flex items-center gap-1.5 text-emerald-400 font-medium">
                <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse"></span>
                Router Mode Active
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
