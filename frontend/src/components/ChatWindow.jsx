import { useState, useRef, useEffect } from 'react';
import Aurora from './Aurora';
import MessageBubble from './MessageBubble';
import {
  AlertCircle,
  ArrowUp,
  Bot,
  Brain,
  Check,
  ChevronDown,
  Code2,
  Cpu,
  FileText,
  Route,
  Send,
  Sparkles,
  Trash2
} from 'lucide-react';

const suggestions = [
  {
    icon: Code2,
    title: 'Debug code',
    text: 'Paste an error, stack trace, or function to improve.'
  },
  {
    icon: Brain,
    title: 'Think through',
    text: 'Break down a plan, tradeoff, or technical decision.'
  },
  {
    icon: FileText,
    title: 'Write better',
    text: 'Draft docs, emails, summaries, and project notes.'
  }
];

const MAX_CONTEXT_MESSAGES = 6;

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
  const messagesContainerRef = useRef(null);
  const textareaRef = useRef(null);

  const hasMessages = (conversation?.messages?.length || 0) > 0;

  const scrollToBottom = (smooth = false) => {
    requestAnimationFrame(() => {
      if (messagesContainerRef.current) {
        messagesContainerRef.current.scrollTo({
          top: messagesContainerRef.current.scrollHeight,
          behavior: smooth ? 'smooth' : 'auto'
        });
      }
    });
  };

  useEffect(() => {
    scrollToBottom(!isStreaming);
  }, [conversation?.messages]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [input]);

  const submitPrompt = async (prompt) => {
    if (!prompt.trim() || isStreaming || !conversation) return;

    const userMessage = {
      role: 'user',
      content: prompt,
      timestamp: new Date()
    };

    const history = conversation.messages
      .slice(-MAX_CONTEXT_MESSAGES)
      .map((msg) => ({
        role: msg.role,
        content: msg.content
      }));

    setInput('');
    setError('');
    onAddMessage(conversation.id, userMessage);
    onAddMessage(conversation.id, {
      role: 'assistant',
      content: '',
      model: selectedModel,
      timestamp: new Date(),
      isStreaming: true
    });
    setIsStreaming(true);

    try {
      const response = await fetch(`${apiUrl}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          prompt,
          model: useRouter ? null : selectedModel,
          use_router: useRouter,
          conversation_id: conversation.id,
          conversation_history: history
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let accumulatedContent = '';
      let actualModel = selectedModel;
      let sseBuffer = '';

      const handleStreamEvent = (event) => {
        const dataLine = event
          .split('\n')
          .find((line) => line.startsWith('data: '));

        if (!dataLine) return;

        try {
          const data = JSON.parse(dataLine.slice(6));
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
      };

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        sseBuffer += decoder.decode(value, { stream: true });
        const events = sseBuffer.split('\n\n');
        sseBuffer = events.pop() || '';
        events.forEach(handleStreamEvent);
      }

      if (sseBuffer.trim()) {
        handleStreamEvent(sseBuffer);
      }
    } catch (err) {
      console.error('Chat error:', err);
      setError('Failed to get response. Make sure Ollama is running and the selected model is installed.');
      onUpdateLastMessage(conversation.id, {
        content: 'Error: Failed to get response. Please check Ollama and your selected model.',
        isStreaming: false,
        error: true
      });
    } finally {
      setIsStreaming(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    submitPrompt(input);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submitPrompt(input);
    }
  };

  if (!conversation) {
    return (
      <main className="flex flex-1 items-center justify-center">
        <div className="text-center">
          <Bot className="mx-auto mb-4 h-10 w-10 text-[#55f3df]" />
          <h2 className="text-xl font-semibold text-white">Preparing your workspace</h2>
          <p className="mt-2 text-sm text-[#80958f]">Loading conversations from persistent memory.</p>
        </div>
      </main>
    );
  }

  return (
    <main className="relative flex h-full flex-1 flex-col overflow-hidden">
      {!hasMessages && (
        <div className="pointer-events-none absolute inset-0 z-0 opacity-90">
          <Aurora
            colorStops={['#24f0df', '#7cff67', '#5227FF']}
            blend={0.55}
            amplitude={1.15}
            speed={0.8}
          />
        </div>
      )}

      <header className="relative z-10 flex h-16 items-center justify-between border-b border-white/[0.06] bg-[#07100f]/45 px-8 backdrop-blur-xl">
        <div>
          <h2 className="text-sm font-medium text-white">{conversation.title || 'New Chat'}</h2>
          <p className="text-xs text-[#70857f]">
            {hasMessages ? `${conversation.messages.length} messages` : 'Start a local conversation'}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="hidden items-center gap-2 rounded-full border border-white/[0.07] bg-white/[0.035] px-3 py-1.5 text-xs text-[#9fb1ad] md:flex">
            <Route className="h-3.5 w-3.5 text-[#55f3df]" />
            {useRouter ? 'Router active' : selectedModel}
          </div>
          {hasMessages && (
            <button
              onClick={onClearChat}
              disabled={isStreaming}
              className="rounded-xl border border-white/[0.07] bg-white/[0.035] p-2 text-[#80958f] transition hover:border-rose-400/25 hover:bg-rose-400/10 hover:text-rose-300 disabled:opacity-50"
              title="Clear chat"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          )}
        </div>
      </header>

      <section ref={messagesContainerRef} className="relative z-10 flex-1 overflow-y-auto px-6">
        {!hasMessages ? (
          <div className="mx-auto flex min-h-full w-full max-w-5xl flex-col justify-center py-10">
            <div className="mb-8 max-w-3xl">
              <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-[#28ead8]/20 bg-[#20dcca]/10 px-3 py-1.5 text-xs text-[#8ffcf0]">
                <Sparkles className="h-3.5 w-3.5" />
                Local models, private memory, streaming responses
              </div>
              <h1 className="text-5xl font-semibold tracking-[-0.04em] text-white md:text-7xl">
                How can I help?
              </h1>
              <p className="mt-4 max-w-2xl text-base leading-7 text-[#9fb1ad]">
                Ask a question, debug code, compare models, or continue building your local AI workspace.
              </p>
            </div>

            <div className="mb-6 grid gap-3 md:grid-cols-3">
              {suggestions.map((suggestion) => {
                const Icon = suggestion.icon;
                return (
                  <button
                    key={suggestion.title}
                    onClick={() => setInput(suggestion.text)}
                    className="group rounded-2xl border border-white/[0.08] bg-[#07100f]/60 p-4 text-left shadow-[0_20px_60px_rgba(0,0,0,0.18)] backdrop-blur-xl transition hover:border-[#28ead8]/25 hover:bg-[#102421]/80"
                  >
                    <div className="mb-4 grid h-9 w-9 place-items-center rounded-xl bg-[#20dcca]/10 text-[#7ffff0] transition group-hover:bg-[#20dcca]/16">
                      <Icon className="h-4 w-4" />
                    </div>
                    <div className="text-sm font-semibold text-white">{suggestion.title}</div>
                    <div className="mt-1 text-sm leading-5 text-[#819690]">{suggestion.text}</div>
                  </button>
                );
              })}
            </div>

            <Composer
              input={input}
              setInput={setInput}
              textareaRef={textareaRef}
              handleSubmit={handleSubmit}
              handleKeyDown={handleKeyDown}
              isStreaming={isStreaming}
              models={models}
              selectedModel={selectedModel}
              onSelectModel={onSelectModel}
              useRouter={useRouter}
              onToggleRouter={onToggleRouter}
              large
            />

            {models.length === 0 && (
              <div className="mt-4 flex items-start gap-3 rounded-2xl border border-amber-300/20 bg-amber-300/8 p-4 text-sm text-amber-100">
                <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" />
                <span>No Ollama models found. Run <code className="rounded bg-black/35 px-1.5 py-0.5">ollama pull llama3.2</code>.</span>
              </div>
            )}
          </div>
        ) : (
          <div className="mx-auto max-w-5xl space-y-6 py-8">
            {conversation.messages.map((message, index) => (
              <MessageBubble
                key={`${conversation.id}-${index}-${message.timestamp?.getTime() || index}`}
                message={message}
              />
            ))}
          </div>
        )}
      </section>

      {error && (
        <div className="relative z-20 border-t border-red-400/20 bg-red-400/8 px-8 py-3 text-sm text-red-200">
          <div className="mx-auto flex max-w-5xl items-center gap-2">
            <AlertCircle className="h-4 w-4" />
            {error}
          </div>
        </div>
      )}

      {hasMessages && (
        <footer className="relative z-20 border-t border-white/[0.06] bg-[#07100f]/75 px-6 py-4 backdrop-blur-2xl">
          <div className="mx-auto max-w-5xl">
            <Composer
              input={input}
              setInput={setInput}
              textareaRef={textareaRef}
              handleSubmit={handleSubmit}
              handleKeyDown={handleKeyDown}
              isStreaming={isStreaming}
              models={models}
              selectedModel={selectedModel}
              onSelectModel={onSelectModel}
              useRouter={useRouter}
              onToggleRouter={onToggleRouter}
            />
          </div>
        </footer>
      )}
    </main>
  );
}

function Composer({
  input,
  setInput,
  textareaRef,
  handleSubmit,
  handleKeyDown,
  isStreaming,
  models,
  selectedModel,
  onSelectModel,
  useRouter,
  onToggleRouter,
  large = false
}) {
  return (
    <form
      onSubmit={handleSubmit}
      className={`rounded-3xl border border-[#28ead8]/18 bg-[#0e2421]/92 shadow-[0_24px_80px_rgba(0,0,0,0.28),inset_0_1px_0_rgba(255,255,255,0.04)] backdrop-blur-2xl ${
        large ? 'p-4' : 'p-3'
      }`}
    >
      <textarea
        ref={textareaRef}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask anything..."
        rows="1"
        disabled={isStreaming}
        className={`max-h-44 w-full resize-none bg-transparent text-[#f4fbf9] outline-none placeholder:text-[#78908a] ${
          large ? 'min-h-[96px] text-lg' : 'min-h-[48px] text-base'
        }`}
      />
      <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <ModelPicker
            models={models}
            selectedModel={selectedModel}
            useRouter={useRouter}
            isStreaming={isStreaming}
            onSelectModel={onSelectModel}
            onToggleRouter={onToggleRouter}
          />
          <button
            type="button"
            onClick={() => onToggleRouter(!useRouter)}
            className={`inline-flex h-9 items-center gap-2 rounded-xl border px-3 text-sm transition ${
              useRouter
                ? 'border-[#28ead8]/20 bg-[#20dcca]/10 text-[#8ffcf0]'
                : 'border-white/[0.08] bg-white/[0.035] text-[#8da19c]'
            }`}
          >
            <Sparkles className="h-3.5 w-3.5" />
            Router
          </button>
        </div>
        <button
          type="submit"
          disabled={!input.trim() || isStreaming || models.length === 0}
          className="grid h-11 w-11 place-items-center rounded-2xl bg-[#20dcca] text-[#06211e] shadow-[0_0_28px_rgba(32,220,202,0.24)] transition hover:bg-[#69f8eb] disabled:cursor-not-allowed disabled:bg-[#23413d] disabled:text-[#6d8985] disabled:shadow-none"
          title="Send"
        >
          {isStreaming ? <Send className="h-5 w-5" /> : <ArrowUp className="h-5 w-5" />}
        </button>
      </div>
    </form>
  );
}

function ModelPicker({
  models,
  selectedModel,
  useRouter,
  isStreaming,
  onSelectModel,
  onToggleRouter
}) {
  const [isOpen, setIsOpen] = useState(false);
  const pickerRef = useRef(null);
  const activeLabel = useRouter || selectedModel === 'auto' ? 'Auto router' : selectedModel;

  useEffect(() => {
    const handlePointerDown = (event) => {
      if (pickerRef.current && !pickerRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('pointerdown', handlePointerDown);
    return () => document.removeEventListener('pointerdown', handlePointerDown);
  }, []);

  const chooseModel = (value) => {
    onSelectModel(value);
    onToggleRouter(value === 'auto');
    setIsOpen(false);
  };

  return (
    <div ref={pickerRef} className="relative">
      <button
        type="button"
        onClick={() => setIsOpen((open) => !open)}
        disabled={isStreaming}
        className="inline-flex h-10 min-w-[190px] items-center justify-between gap-3 rounded-xl border border-[#28ead8]/16 bg-[#07100f]/80 px-3 text-sm text-[#d7e6e2] shadow-[inset_0_1px_0_rgba(255,255,255,0.04)] outline-none transition hover:border-[#28ead8]/34 hover:bg-[#0c1716] disabled:cursor-not-allowed disabled:opacity-50"
        aria-haspopup="listbox"
        aria-expanded={isOpen}
      >
        <span className="flex min-w-0 items-center gap-2">
          {useRouter || selectedModel === 'auto' ? (
            <Sparkles className="h-4 w-4 flex-shrink-0 text-[#71fff1]" />
          ) : (
            <Cpu className="h-4 w-4 flex-shrink-0 text-[#71fff1]" />
          )}
          <span className="truncate">{activeLabel}</span>
        </span>
        <ChevronDown className={`h-4 w-4 flex-shrink-0 text-[#78908a] transition ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div
          className="absolute bottom-[calc(100%+10px)] left-0 z-50 w-[300px] overflow-hidden rounded-2xl border border-[#28ead8]/22 bg-[#07100f] p-1.5 shadow-[0_28px_90px_rgba(0,0,0,0.7),0_0_0_1px_rgba(255,255,255,0.035),inset_0_1px_0_rgba(255,255,255,0.05)]"
          role="listbox"
        >
          <ModelOption
            active={useRouter || selectedModel === 'auto'}
            icon={Sparkles}
            title="Auto router"
            detail="Pick the model per prompt"
            onClick={() => chooseModel('auto')}
          />

          <div className="my-1 h-px bg-white/[0.06]" />

          <div className="max-h-60 overflow-y-auto pr-1">
            {models.length === 0 ? (
              <div className="px-3 py-4 text-sm text-[#78908a]">No local models found</div>
            ) : (
              models.map((model) => (
                <ModelOption
                  key={model.name}
                  active={!useRouter && selectedModel === model.name}
                  icon={Cpu}
                  title={model.name}
                  detail={formatModelSize(model.size)}
                  onClick={() => chooseModel(model.name)}
                />
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function ModelOption({ active, icon: Icon, title, detail, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left transition ${
        active
          ? 'bg-[#20dcca]/14 text-[#eafffc]'
          : 'text-[#b8cbc6] hover:bg-white/[0.045] hover:text-white'
      }`}
      role="option"
      aria-selected={active}
    >
      <span
        className={`grid h-8 w-8 flex-shrink-0 place-items-center rounded-lg border ${
          active
            ? 'border-[#28ead8]/28 bg-[#20dcca]/16 text-[#8ffcf0]'
            : 'border-white/[0.07] bg-white/[0.035] text-[#78908a]'
        }`}
      >
        <Icon className="h-4 w-4" />
      </span>
      <span className="min-w-0 flex-1">
        <span className="block truncate text-sm font-medium">{title}</span>
        {detail && <span className="block truncate text-xs text-[#78908a]">{detail}</span>}
      </span>
      {active && <Check className="h-4 w-4 flex-shrink-0 text-[#8ffcf0]" />}
    </button>
  );
}

function formatModelSize(size) {
  if (!size) return 'Local model';
  const gb = size / 1024 ** 3;
  if (gb >= 1) return `${gb.toFixed(gb >= 10 ? 0 : 1)} GB`;
  return `${(size / 1024 ** 2).toFixed(0)} MB`;
}
