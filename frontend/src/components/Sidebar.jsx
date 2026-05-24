import {
  Bot,
  Database,
  MessageCircle,
  Plus,
  RefreshCw,
  Settings,
  Sparkles,
  Trash2,
  Wifi,
  WifiOff
} from 'lucide-react';

export default function Sidebar({
  conversations,
  currentConversationId,
  onSelectConversation,
  onNewConversation,
  onDeleteConversation,
  models,
  useRouter,
  onToggleRouter,
  activeTab,
  onTabChange,
  ollamaStatus,
  onRefresh
}) {
  const navItems = [
    { id: 'chat', label: 'Chat', icon: MessageCircle },
    { id: 'models', label: 'Models', icon: Database },
    { id: 'settings', label: 'Settings', icon: Settings }
  ];

  return (
    <aside className="relative z-20 flex h-full w-[292px] flex-col border-r border-white/[0.08] bg-[#07100f]/88 backdrop-blur-2xl">
      <div className="border-b border-white/[0.08] p-5">
        <div className="mb-5 flex items-center gap-3">
          <div className="grid h-10 w-10 place-items-center rounded-xl border border-[#28ead8]/25 bg-[#20dcca]/10 shadow-[0_0_30px_rgba(32,220,202,0.12)]">
            <Bot className="h-5 w-5 text-[#72fff0]" />
          </div>
          <div>
            <h1 className="text-base font-semibold text-white">LocalGPT</h1>
            <p className="text-xs text-[#7f9590]">Private local AI workspace</p>
          </div>
        </div>

        <div className="flex items-center justify-between rounded-xl border border-white/[0.07] bg-white/[0.035] px-3 py-2.5">
          <div className="flex items-center gap-2">
            {ollamaStatus === 'running' ? (
              <Wifi className="h-4 w-4 text-[#55f3df]" />
            ) : (
              <WifiOff className="h-4 w-4 text-rose-300" />
            )}
            <span className="text-xs text-[#cbdad6]">
              {ollamaStatus === 'running' ? 'Ollama connected' : ollamaStatus === 'checking' ? 'Checking Ollama' : 'Ollama offline'}
            </span>
          </div>
          <button
            onClick={onRefresh}
            className="rounded-lg p-1.5 text-[#7f9590] transition hover:bg-white/[0.06] hover:text-[#72fff0]"
            title="Refresh status"
          >
            <RefreshCw className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      <nav className="space-y-1 p-3">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onTabChange(item.id)}
              className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition ${
                isActive
                  ? 'border border-[#28ead8]/20 bg-[#20dcca]/10 text-[#91fff3] shadow-[0_0_24px_rgba(32,220,202,0.08)]'
                  : 'border border-transparent text-[#8da19c] hover:bg-white/[0.045] hover:text-[#e6f2ef]'
              }`}
            >
              <Icon className="h-4 w-4" />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="px-4 pb-3 pt-2">
        <button
          onClick={onNewConversation}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-[#20dcca] px-3 py-2.5 text-sm font-semibold text-[#06211e] shadow-[0_14px_35px_rgba(32,220,202,0.18)] transition hover:bg-[#62f8e9]"
        >
          <Plus className="h-4 w-4" />
          New chat
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-3 pb-3">
        <div className="mb-2 flex items-center justify-between px-1">
          <span className="text-xs font-medium uppercase tracking-[0.16em] text-[#657974]">Conversations</span>
          <span className="rounded-full bg-white/[0.05] px-2 py-0.5 text-[10px] text-[#8da19c]">{conversations.length}</span>
        </div>

        <div className="space-y-1.5">
          {conversations.map((conv) => (
            <div
              key={conv.id}
              className={`group flex items-center gap-2 rounded-xl border px-3 py-2.5 transition ${
                conv.id === currentConversationId
                  ? 'border-[#28ead8]/18 bg-[#13302d] text-white'
                  : 'border-transparent bg-transparent text-[#91a49f] hover:border-white/[0.06] hover:bg-white/[0.035] hover:text-[#edf7f4]'
              }`}
            >
              <button
                onClick={() => onSelectConversation(conv.id)}
                className="min-w-0 flex-1 text-left"
              >
                <div className="truncate text-sm">{conv.title}</div>
                <div className="mt-0.5 text-[11px] text-[#657974]">
                  {conv.messages?.length || 0} messages
                </div>
              </button>
              {conversations.length > 1 && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteConversation(conv.id);
                  }}
                  className="rounded-lg p-1.5 text-[#637772] opacity-0 transition hover:bg-rose-400/10 hover:text-rose-300 group-hover:opacity-100"
                  title="Delete conversation"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="border-t border-white/[0.08] p-4">
        <button
          onClick={() => onToggleRouter(!useRouter)}
          className={`mb-3 flex w-full items-center justify-between rounded-xl border px-3 py-2.5 text-sm transition ${
            useRouter
              ? 'border-[#28ead8]/18 bg-[#20dcca]/9 text-[#91fff3]'
              : 'border-white/[0.07] bg-white/[0.035] text-[#8da19c]'
          }`}
        >
          <span className="flex items-center gap-2">
            <Sparkles className="h-4 w-4" />
            Router mode
          </span>
          <span className={`h-2 w-2 rounded-full ${useRouter ? 'bg-[#20dcca]' : 'bg-[#637772]'}`} />
        </button>
        <div className="flex items-center justify-between text-xs text-[#657974]">
          <span>{models.length} local models</span>
          <span>SQLite memory</span>
        </div>
      </div>
    </aside>
  );
}
