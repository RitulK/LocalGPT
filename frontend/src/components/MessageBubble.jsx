import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Copy, Check, User, Bot, ExternalLink, BookOpen } from 'lucide-react';

const normalizeMarkdownTables = (content) => (
  content
    .replace(/\s+\|\|\s+/g, '\n| ')
    .replace(/(\|[^\n|]+(?:\|[^\n|]+)+\|?)\s+(\|?\s*:?-{3,}:?\s*\|)/g, '$1\n$2')
);

export default function MessageBubble({ message, apiUrl, onReadObsidianNote }) {
  const [copied, setCopied] = useState(false);
  const [actionError, setActionError] = useState('');

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const isUser = message.role === 'user';
  const openInObsidian = async (path) => {
    try {
      const response = await fetch(`${apiUrl}/obsidian/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'open', path })
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || 'Could not open in Obsidian');
      setActionError('');
    } catch (error) {
      setActionError(error.message);
    }
  };
  const searchResults = (message.obsidianSearchResults || []).map((result) => ({
    path: typeof result === 'string' ? result : result.filename || result.path,
    excerpt: typeof result === 'object'
      ? result.matches?.[0]?.context || result.snippet || ''
      : ''
  })).filter((result) => result.path);

  return (
    <div className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'} group animate-in fade-in slide-in-from-bottom-4 duration-500`}>
      {!isUser && (
        <div className="flex-shrink-0 w-7 h-7 rounded-[7px] bg-[#10211f] border border-[#2af0dc]/15 flex items-center justify-center shadow-[0_0_18px_rgba(32,220,202,0.08)] group-hover:border-[#2af0dc]/35 transition">
          <Bot className="w-3.5 h-3.5 text-[#78fff0]" />
        </div>
      )}
      
      <div className={`flex-1 max-w-3xl ${isUser ? 'flex flex-col items-end' : ''}`}>
        {/* Model indicator for assistant */}
        {!isUser && message.model && (
          <div className="text-[10px] text-[#667b76] mb-1 flex items-center gap-2">
            <span>{message.model}</span>
            {message.isStreaming && (
              <span className="flex items-center gap-1">
                <span className="animate-pulse">●</span>
                Streaming...
              </span>
            )}
          </div>
        )}
        
        <div
          className={`rounded-[10px] px-4 py-3 shadow-lg transition-all duration-300 text-sm ${
            isUser
              ? 'bg-[#20dcca] text-[#061d1a] shadow-[0_12px_30px_rgba(32,220,202,0.16)]'
              : message.error
              ? 'bg-red-500/10 border border-red-500/30 text-red-200'
              : 'bg-[#111c1b]/95 text-[#dfece8] border border-white/[0.06] hover:border-[#2af0dc]/15'
          }`}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="markdown-content prose prose-invert max-w-none">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  table({ children, ...props }) {
                    return (
                      <div className="markdown-table-wrap">
                        <table {...props}>{children}</table>
                      </div>
                    );
                  },
                  code({ node, inline, className, children, ...props }) {
                    const match = /language-(\w+)/.exec(className || '');
                    const codeString = String(children).replace(/\n$/, '');
                    
                    return !inline && match ? (
                      <div className="relative group">
                        <button
                          onClick={() => copyToClipboard(codeString)}
                          className="absolute right-2 top-2 p-2 rounded bg-[#132522] hover:bg-[#1a3430] transition opacity-0 group-hover:opacity-100"
                          title="Copy code"
                        >
                          {copied ? (
                            <Check className="w-4 h-4 text-green-400" />
                          ) : (
                            <Copy className="w-4 h-4 text-gray-300" />
                          )}
                        </button>
                        <SyntaxHighlighter
                          style={vscDarkPlus}
                          language={match[1]}
                          PreTag="div"
                          {...props}
                        >
                          {codeString}
                        </SyntaxHighlighter>
                      </div>
                    ) : (
                      <code className={className} {...props}>
                        {children}
                      </code>
                    );
                  },
                }}
              >
                {normalizeMarkdownTables(message.content || (message.isStreaming ? '...' : ''))}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {/* Copy button for assistant messages */}
        {!isUser && message.content && !message.isStreaming && (
          <button
            onClick={() => copyToClipboard(message.content)}
            className="mt-2 text-[10px] text-[#667b76] hover:text-[#8ffcf0] flex items-center gap-1 transition"
          >
            {copied ? (
              <>
                <Check className="w-3 h-3" />
                Copied!
              </>
            ) : (
              <>
                <Copy className="w-3 h-3" />
                Copy response
              </>
            )}
          </button>
        )}

        {!isUser && message.obsidianOpenPath && !message.isStreaming && (
          <button
            onClick={() => openInObsidian(message.obsidianOpenPath)}
            className="mt-2 inline-flex items-center gap-2 rounded-lg border border-[#28ead8]/20 bg-[#20dcca]/8 px-2.5 py-1.5 text-[10px] font-semibold text-[#8ffcf0]"
          >
            <ExternalLink className="h-3 w-3" />
            Open in Obsidian
          </button>
        )}

        {!isUser && searchResults.length > 0 && (
          <div className="mt-3 space-y-2">
            {searchResults.map((result, index) => (
              <div key={`${result.path}-${index}`} className="rounded-xl border border-white/[0.08] bg-[#0b1716] p-3">
                <div className="break-all text-xs font-semibold text-[#dce9e5]">{result.path}</div>
                {result.excerpt && <p className="mt-1 line-clamp-3 text-xs leading-5 text-[#91a49f]">{result.excerpt}</p>}
                <div className="mt-2 flex gap-2">
                  <button
                    type="button"
                    onClick={() => onReadObsidianNote?.(result.path)}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-[#28ead8]/20 px-2.5 py-1.5 text-[10px] font-semibold text-[#8ffcf0]"
                  >
                    <BookOpen className="h-3 w-3" />
                    Read in chat
                  </button>
                  <button
                    type="button"
                    onClick={() => openInObsidian(result.path)}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-white/[0.08] px-2.5 py-1.5 text-[10px] text-[#b9c9c5]"
                  >
                    <ExternalLink className="h-3 w-3" />
                    Open in Obsidian
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
        {actionError && <p className="mt-2 text-xs text-rose-300">{actionError}</p>}

        {/* Timestamp */}
        <div className="text-[10px] text-[#536560] mt-1">
          {message.timestamp?.toLocaleTimeString()}
        </div>
      </div>

      {isUser && (
        <div className="flex-shrink-0 w-7 h-7 rounded-[7px] bg-[#14201f] border border-white/[0.06] flex items-center justify-center shadow-lg">
          <User className="w-3.5 h-3.5 text-[#d7e6e2]" />
        </div>
      )}
    </div>
  );
}
