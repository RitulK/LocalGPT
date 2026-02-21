import { MessageSquare, Plus, Trash2, MessageCircle, Settings, Database } from 'lucide-react';

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
    <div className="w-80 bg-slate-900/50 backdrop-blur-xl border-r border-slate-700/50 flex flex-col shadow-2xl">
      {/* Tab Navigation */}
      <div className="flex border-b border-slate-700/50">
        <button
          onClick={() => onTabChange('chat')}
          className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 transition-all duration-300 ${
            activeTab === 'chat'
              ? 'bg-gradient-to-b from-indigo-600/20 to-transparent text-indigo-400 border-b-2 border-indigo-500 shadow-lg shadow-indigo-500/10'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
          }`}
        >
          <MessageCircle className="w-4 h-4" />
          <span className="text-sm font-medium">Chat</span>
        </button>
        <button
          onClick={() => onTabChange('models')}
          className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 transition-all duration-300 ${
            activeTab === 'models'
              ? 'bg-gradient-to-b from-indigo-600/20 to-transparent text-indigo-400 border-b-2 border-indigo-500 shadow-lg shadow-indigo-500/10'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
          }`}
        >
          <Database className="w-4 h-4" />
          <span className="text-sm font-medium">Models</span>
        </button>
        <button
          onClick={() => onTabChange('settings')}
          className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 transition-all duration-300 ${
            activeTab === 'settings'
              ? 'bg-gradient-to-b from-indigo-600/20 to-transparent text-indigo-400 border-b-2 border-indigo-500 shadow-lg shadow-indigo-500/10'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
          }`}
        >
          <Settings className="w-4 h-4" />
          <span className="text-sm font-medium">Settings</span>
        </button>
      </div>

      {/* Model Selector */}
      <div className="p-4 border-b border-slate-700/50 bg-slate-900/30">
        <label className="block text-sm font-medium text-slate-200 mb-2">
          Model Selection
        </label>
        <select
          value={selectedModel}
          onChange={(e) => {
            const value = e.target.value;
            onSelectModel(value);
            onToggleRouter(value === 'auto');
          }}
          className="w-full bg-slate-800/80 text-slate-100 rounded-xl px-4 py-3 text-sm border border-slate-700/50 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50 transition-all duration-300 backdrop-blur-sm cursor-pointer"
        >
          <option value="auto">🤖 Auto (Router Mode)</option>
          <option disabled>──────────</option>
          {models.map((model) => (
            <option key={model.name} value={model.name}>
              {model.name}
            </option>
          ))}
        </select>
        
        {selectedModel === 'auto' && (
          <div className="mt-3 p-3 bg-indigo-500/10 border border-indigo-500/30 rounded-xl">
            <p className="text-xs text-indigo-300">
              ✨ Automatically selects the best model based on your prompt
            </p>
          </div>
        )}
      </div>

      {/* Conversations List */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-4">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-slate-200">Conversations</h2>
            <button
              onClick={onNewConversation}
              className="p-2 rounded-xl hover:bg-indigo-600/20 transition-all duration-300 text-slate-400 hover:text-indigo-400 border border-transparent hover:border-indigo-500/30"
              title="New Conversation"
            >
              <Plus className="w-4 h-4" />
            </button>
          </div>
          
          <div className="space-y-2">
            {conversations.map((conv) => (
              <div
                key={conv.id}
                className={`group relative flex items-center gap-3 p-3 rounded-xl cursor-pointer transition-all duration-300 border ${
                  conv.id === currentConversationId
                    ? 'bg-gradient-to-r from-indigo-600/20 to-purple-600/20 border-indigo-500/50 shadow-lg shadow-indigo-500/10 text-slate-100'
                    : 'bg-slate-800/40 border-slate-700/30 hover:bg-slate-800/70 hover:border-slate-600/50 text-slate-400 hover:text-slate-200'
                }`}
                onClick={() => onSelectConversation(conv.id)}
              >
                <MessageSquare className="w-4 h-4 flex-shrink-0" />
                <span className="flex-1 text-sm truncate">{conv.title}</span>
                {conversations.length > 1 && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteConversation(conv.id);
                    }}
                    className="opacity-0 group-hover:opacity-100 p-1.5 rounded-lg hover:bg-red-500/20 transition-all duration-300 text-slate-400 hover:text-red-400"
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
      <div className="p-4 border-t border-slate-700/50 text-xs text-slate-400 bg-slate-900/30">
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
