import { MessageSquare, Plus, Trash2, MessageCircle, Database } from 'lucide-react';

export default function Sidebar({
  conversations,
  currentConversationId,
  onSelectConversation,
  onNewConversation,
  onDeleteConversation,
  models,
  selectedModel,
  onSelectModel,
  useRouter,
  onToggleRouter,
  activeTab,
  onTabChange,
  ollamaStatus,
  onRefresh
}) {
  return (
    <div className="w-80 bg-white/5 border-r border-white/15 flex flex-col shadow-lg backdrop-blur-sm" style={{
      background: 'rgba(15, 23, 42, 0.8)',
      backdropFilter: 'blur(20px) saturate(150%)',
      WebkitBackdropFilter: 'blur(20px) saturate(150%)',
    }}>
      {/* Tab Navigation */}
      <div className="flex border-b border-white/15">
        <button
          onClick={() => onTabChange('chat')}
          className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 transition-all duration-300 ${
            activeTab === 'chat'
              ? 'bg-white/10 text-indigo-300 border-b-2 border-indigo-400 shadow-lg shadow-indigo-500/20'
              : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
          }`}
        >
          <MessageCircle className="w-4 h-4" />
          <span className="text-sm font-medium">Chat</span>
        </button>
        <button
          onClick={() => onTabChange('models')}
          className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 transition-all duration-300 ${
            activeTab === 'models'
              ? 'bg-white/10 text-indigo-300 border-b-2 border-indigo-400 shadow-lg shadow-indigo-500/20'
              : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
          }`}
        >
          <Database className="w-4 h-4" />
          <span className="text-sm font-medium">Models</span>
        </button>
      </div>

      {/* Model Selector - Minimal Info */}
      <div className="px-4 py-3 border-b border-white/15 bg-white/5" style={{
        backdropFilter: 'blur(10px)',
      }}>
        <div className="flex items-center justify-between">
          <label className="block text-sm font-medium text-slate-300">
            Status
          </label>
          <div className="flex items-center gap-2 px-2.5 py-1.5 rounded-full bg-white/10 border border-white/20" style={{
            backdropFilter: 'blur(10px)',
          }}>
            <div className={`w-2 h-2 rounded-full ${
              useRouter 
                ? 'bg-emerald-500 shadow-lg shadow-emerald-500/50 animate-pulse' 
                : 'bg-blue-500 shadow-lg shadow-blue-500/50 animate-pulse'
            }`} />
            <span className="text-xs font-medium text-slate-300">
              {useRouter ? 'Router' : 'Custom'}
            </span>
          </div>
        </div>
      </div>

      {/* Conversations List */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-4">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-slate-200">Conversations</h2>
            <button
              onClick={onNewConversation}
              className="p-2 rounded-lg hover:bg-white/10 transition-all duration-300 text-slate-400 hover:text-indigo-300 border border-transparent hover:border-indigo-400/40"
              title="New Conversation"
              style={{
                backdropFilter: 'blur(10px)',
              }}
            >
              <Plus className="w-4 h-4" />
            </button>
          </div>
          
          <div className="space-y-2">
            {conversations.map((conv) => (
              <div
                key={conv.id}
                className={`group relative flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-all duration-300 border ${
                  conv.id === currentConversationId
                    ? 'bg-white/15 border-indigo-400/50 shadow-lg shadow-indigo-500/10 text-slate-100'
                    : 'bg-white/5 border-white/10 hover:bg-white/10 hover:border-white/30 text-slate-400 hover:text-slate-200'
                }`}
                onClick={() => onSelectConversation(conv.id)}
                style={{
                  backdropFilter: 'blur(10px)',
                }}
              >
                <MessageSquare className="w-4 h-4 flex-shrink-0" />
                <span className="flex-1 text-sm truncate">{conv.title}</span>
                {conversations.length > 1 && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteConversation(conv.id);
                    }}
                    className="opacity-0 group-hover:opacity-100 p-1.5 rounded-md hover:bg-red-500/20 transition-all duration-300 text-slate-400 hover:text-red-400"
                    title="Delete Conversation"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Footer Info */}
      <div className="p-4 border-t border-white/15 text-xs text-slate-400 bg-white/5" style={{
        backdropFilter: 'blur(10px)',
      }}>
        <div className="flex items-center justify-between mb-2">
          <span className="font-medium">Models: <span className="text-indigo-400">{models.length}</span></span>
          <button
            onClick={onRefresh}
            className="text-indigo-400 hover:text-indigo-300 transition-colors duration-300 font-medium"
          >
            Refresh
          </button>
        </div>
        <div className="font-medium">Conversations: <span className="text-indigo-400">{conversations.length}</span></div>
      </div>
    </div>
  );
}
