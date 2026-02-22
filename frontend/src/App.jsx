import { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import ChatWindow from './components/ChatWindow';
import SettingsPanel from './components/SettingsPanel';
import ModelManagement from './components/ModelManagement';
import { Bot, Settings, Database } from 'lucide-react';

function App() {
  const [conversations, setConversations] = useState([
    { id: 1, title: 'New Chat', messages: [], createdAt: new Date() }
  ]);
  const [currentConversationId, setCurrentConversationId] = useState(1);
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState('auto');
  const [useRouter, setUseRouter] = useState(true);
  const [settings, setSettings] = useState({
    default_general_model: 'qwen:4b',
    default_coding_model: 'qwen:4b',
    default_reasoning_model: 'qwen:4b',
    router_enabled: true
  });
  const [activeTab, setActiveTab] = useState('chat'); // chat, settings, models
  const [darkMode, setDarkMode] = useState(true);
  const [ollamaStatus, setOllamaStatus] = useState('checking');

  const currentConversation = conversations.find(c => c.id === currentConversationId);

  // Fetch models on mount
  useEffect(() => {
    fetchModels();
    checkOllamaHealth();
  }, []);

  const checkOllamaHealth = async () => {
    try {
      const response = await fetch('http://localhost:8000/health');
      const data = await response.json();
      setOllamaStatus(data.ollama_running ? 'running' : 'stopped');
    } catch (error) {
      setOllamaStatus('error');
    }
  };

  const fetchModels = async () => {
    try {
      const response = await fetch('http://localhost:8000/models');
      const data = await response.json();
      setModels(data.models || []);
      
      // Set default model if auto is selected and models exist
      if (data.models && data.models.length > 0 && !selectedModel) {
        setSelectedModel('auto');
      }
    } catch (error) {
      console.error('Failed to fetch models:', error);
    }
  };

  const createNewConversation = () => {
    const newId = Math.max(...conversations.map(c => c.id), 0) + 1;
    const newConv = {
      id: newId,
      title: 'New Chat',
      messages: [],
      createdAt: new Date()
    };
    setConversations([...conversations, newConv]);
    setCurrentConversationId(newId);
  };

  const deleteConversation = (id) => {
    if (conversations.length === 1) {
      // Don't delete the last conversation, just clear it
      setConversations([{ id: 1, title: 'New Chat', messages: [], createdAt: new Date() }]);
      setCurrentConversationId(1);
    } else {
      const filtered = conversations.filter(c => c.id !== id);
      setConversations(filtered);
      if (currentConversationId === id) {
        setCurrentConversationId(filtered[0].id);
      }
    }
  };

  const updateConversation = (id, updates) => {
    setConversations(prevConversations => prevConversations.map(c => 
      c.id === id ? { ...c, ...updates } : c
    ));
  };

  const addMessage = (conversationId, message) => {
    setConversations(prevConversations => {
      const conv = prevConversations.find(c => c.id === conversationId);
      if (!conv) return prevConversations;
      
      const updatedMessages = [...conv.messages, message];
      
      // Update title if it's the first user message
      let title = conv.title;
      if (conv.messages.length === 0 && message.role === 'user') {
        title = message.content.slice(0, 50) + (message.content.length > 50 ? '...' : '');
      }
      
      return prevConversations.map(c => 
        c.id === conversationId ? { ...c, messages: updatedMessages, title } : c
      );
    });
  };

  const updateLastMessage = (conversationId, updates) => {
    setConversations(prevConversations => {
      const conv = prevConversations.find(c => c.id === conversationId);
      if (!conv || conv.messages.length === 0) return prevConversations;
      
      const updatedMessages = [...conv.messages];
      updatedMessages[updatedMessages.length - 1] = {
        ...updatedMessages[updatedMessages.length - 1],
        ...updates
      };
      
      return prevConversations.map(c => 
        c.id === conversationId ? { ...c, messages: updatedMessages } : c
      );
    });
  };

  const clearCurrentChat = () => {
    updateConversation(currentConversationId, { 
      messages: [], 
      title: 'New Chat' 
    });
  };

  return (
    <div className={`flex h-screen overflow-hidden ${darkMode ? 'dark' : ''}`}>
      <div className="flex w-full bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-gray-100 overflow-hidden">
        {/* Sidebar */}
        <Sidebar
          conversations={conversations}
          currentConversationId={currentConversationId}
          onSelectConversation={setCurrentConversationId}
          onNewConversation={createNewConversation}
          onDeleteConversation={deleteConversation}
          models={models}
          selectedModel={selectedModel}
          onSelectModel={setSelectedModel}
          useRouter={useRouter}
          onToggleRouter={setUseRouter}
          activeTab={activeTab}
          onTabChange={setActiveTab}
          ollamaStatus={ollamaStatus}
          onRefresh={checkOllamaHealth}
        />

        {/* Main Content */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Header */}
          <div className="bg-slate-900/50 backdrop-blur-xl border-b border-slate-700/50 px-6 py-4 flex items-center justify-between flex-shrink-0 shadow-lg">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-lg shadow-indigo-500/30">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
                  LocalGPT
                </h1>
                <p className="text-xs text-slate-400">your offline AI buddy</p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-800/50 border border-slate-700/50">
                <div className={`w-2 h-2 rounded-full ${
                  ollamaStatus === 'running' ? 'bg-emerald-500 shadow-lg shadow-emerald-500/50 animate-pulse' : 
                  ollamaStatus === 'checking' ? 'bg-amber-500 shadow-lg shadow-amber-500/50 animate-pulse' : 'bg-rose-500'
                }`} />
                <span className="text-xs font-medium text-slate-300">
                  {ollamaStatus === 'running' ? 'Connected' : 
                   ollamaStatus === 'checking' ? 'Checking...' : 'Offline'}
                </span>
              </div>
              <button
                onClick={() => setDarkMode(!darkMode)}
                className="p-2 rounded-xl hover:bg-slate-800/50 transition-all duration-300 border border-transparent hover:border-slate-700/50"
              >
                {darkMode ? '🌙' : '☀️'}
              </button>
            </div>
          </div>

          {/* Content Area */}
          {activeTab === 'chat' && (
            <ChatWindow
              conversation={currentConversation}
              onAddMessage={addMessage}
              onUpdateLastMessage={updateLastMessage}
              onClearChat={clearCurrentChat}
              selectedModel={selectedModel}
              useRouter={useRouter}
              models={models}
            />
          )}

          {activeTab === 'settings' && (
            <SettingsPanel
              settings={settings}
              onUpdateSettings={setSettings}
              models={models}
            />
          )}

          {activeTab === 'models' && (
            <ModelManagement
              models={models}
              onRefresh={fetchModels}
              selectedModel={selectedModel}
            />
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
