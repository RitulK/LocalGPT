import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Copy, Check, User, Bot } from 'lucide-react';

export default function MessageBubble({ message }) {
  const [copied, setCopied] = useState(false);

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const isUser = message.role === 'user';

  return (
    <div className={`flex gap-4 ${isUser ? 'justify-end' : 'justify-start'} group animate-in fade-in slide-in-from-bottom-4 duration-500`}>
      {!isUser && (
        <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/20 group-hover:scale-110 transition-transform duration-300">
          <Bot className="w-5 h-5 text-white" />
        </div>
      )}
      
      <div className={`flex-1 max-w-3xl ${isUser ? 'flex flex-col items-end' : ''}`}>
        {/* Model indicator for assistant */}
        {!isUser && message.model && (
          <div className="text-xs text-gray-500 mb-1 flex items-center gap-2">
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
          className={`rounded-2xl px-5 py-4 shadow-lg transition-all duration-300 ${
            isUser
              ? 'bg-gradient-to-br from-indigo-600 to-purple-600 text-white shadow-indigo-500/30 hover:shadow-indigo-500/40'
              : message.error
              ? 'bg-red-900/20 border border-red-700/50 text-red-300 backdrop-blur-sm'
              : 'bg-slate-800/80 text-gray-100 backdrop-blur-sm border border-slate-700/50 hover:border-slate-600/50'
          }`}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="markdown-content prose prose-invert max-w-none">
              <ReactMarkdown
                components={{
                  code({ node, inline, className, children, ...props }) {
                    const match = /language-(\w+)/.exec(className || '');
                    const codeString = String(children).replace(/\n$/, '');
                    
                    return !inline && match ? (
                      <div className="relative group">
                        <button
                          onClick={() => copyToClipboard(codeString)}
                          className="absolute right-2 top-2 p-2 rounded bg-gray-700 hover:bg-gray-600 transition opacity-0 group-hover:opacity-100"
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
                {message.content || (message.isStreaming ? '...' : '')}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {/* Copy button for assistant messages */}
        {!isUser && message.content && !message.isStreaming && (
          <button
            onClick={() => copyToClipboard(message.content)}
            className="mt-2 text-xs text-gray-500 hover:text-gray-300 flex items-center gap-1 transition"
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

        {/* Timestamp */}
        <div className="text-xs text-gray-500 mt-1">
          {message.timestamp?.toLocaleTimeString()}
        </div>
      </div>

      {isUser && (
        <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-gradient-to-br from-slate-600 to-slate-700 flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform duration-300">
          <User className="w-5 h-5 text-white" />
        </div>
      )}
    </div>
  );
}
