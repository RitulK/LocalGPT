import { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import ChatWindow from './components/ChatWindow';
import ModelManagement from './components/ModelManagement';
import { Bot, Menu, X } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const hydrateConversation = (conversation) => ({
  id: conversation.id,
  title: conversation.title,
  createdAt: new Date(conversation.created_at),
  updatedAt: new Date(conversation.updated_at),
  messages: (conversation.messages || []).map((message) => ({
    role: message.role,
    content: message.content,
    model: message.model,
    timestamp: new Date(message.created_at)
  }))
});

function App() {
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState('auto');
  const [useRouter, setUseRouter] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activeTab, setActiveTab] = useState('chat'); // chat, models
  const [ollamaStatus, setOllamaStatus] = useState('checking');

  const currentConversation = conversations.find(c => c.id === currentConversationId);

  // Fetch models on mount
  useEffect(() => {
    fetchConversations();
    fetchModels();
    checkOllamaHealth();
  }, []);

  const checkOllamaHealth = async () => {
    try {
      const response = await fetch(`${API_URL}/health`);
      const data = await response.json();
      setOllamaStatus(data.ollama_running ? 'running' : 'stopped');
    } catch (error) {
      setOllamaStatus('error');
    }
  };

  const fetchModels = async () => {
    try {
      const response = await fetch(`${API_URL}/models`);
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

  const fetchConversations = async () => {
    try {
      const response = await fetch(`${API_URL}/conversations`);
      const data = await response.json();
      const savedConversations = (data.conversations || []).map(hydrateConversation);

      if (savedConversations.length > 0) {
        setConversations(savedConversations);
        setCurrentConversationId(savedConversations[0].id);
      } else {
        await createNewConversation();
      }
    } catch (error) {
      console.error('Failed to fetch conversations:', error);
      const fallbackConversation = {
        id: Date.now(),
        title: 'New Chat',
        messages: [],
        createdAt: new Date()
      };
      setConversations([fallbackConversation]);
      setCurrentConversationId(fallbackConversation.id);
    }
  };

  const createNewConversation = async () => {
    try {
      const response = await fetch(`${API_URL}/conversations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ title: 'New Chat' }),
      });
      const data = await response.json();
      const newConv = hydrateConversation(data.conversation);
      setConversations(prev => [newConv, ...prev]);
      setCurrentConversationId(newConv.id);
    } catch (error) {
      console.error('Failed to create conversation:', error);
      const newId = Math.max(...conversations.map(c => c.id), 0) + 1;
      const newConv = {
        id: newId,
        title: 'New Chat',
        messages: [],
        createdAt: new Date()
      };
      setConversations([...conversations, newConv]);
      setCurrentConversationId(newId);
    }
  };

  const deleteConversation = async (id) => {
    try {
      await fetch(`${API_URL}/conversations/${id}`, {
        method: 'DELETE',
      });
    } catch (error) {
      console.error('Failed to delete conversation:', error);
    }

    if (conversations.length === 1) {
      // Don't delete the last conversation, just clear it
      await createNewConversation();
      setConversations(prev => prev.filter(c => c.id !== id));
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

  const clearCurrentChat = async () => {
    try {
      await fetch(`${API_URL}/conversations/${currentConversationId}/messages`, {
        method: 'DELETE',
      });
    } catch (error) {
      console.error('Failed to clear conversation:', error);
    }

    updateConversation(currentConversationId, { 
      messages: [], 
      title: 'New Chat' 
    });
  };

  return (
    <div className="flex h-screen overflow-hidden">
      <div className="flex w-full bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-gray-100 overflow-hidden">
        {/* Sidebar */}
        {sidebarOpen && (
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
        )}

        {/* Main Content */}
        <div className="flex-1 flex flex-col overflow-hidden w-full">
          {/* Header */}
          <div className="bg-white/10 backdrop-blur-2xl border-b border-white/20 px-6 py-4 flex items-center justify-between flex-shrink-0 shadow-lg w-full" style={{
            backdropFilter: 'blur(40px) saturate(180%)',
            WebkitBackdropFilter: 'blur(40px) saturate(180%)',
          }}>
            <div className="flex items-center gap-3">
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="w-10 h-10 -ml-2 flex items-center justify-center rounded-lg hover:bg-white/10 transition-colors text-slate-300 hover:text-white"
                title={sidebarOpen ? "Hide Sidebar" : "Show Sidebar"}
              >
                {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
              </button>
              <div className="p-2 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-lg shadow-indigo-500/30">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold bg-gradient-to-r from-indigo-300 to-purple-300 bg-clip-text text-transparent">
                  LocalGPT
                </h1>
                <p className="text-xs text-slate-300">your offline AI buddy</p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/10 border border-white/20" style={{
                backdropFilter: 'blur(20px) saturate(180%)',
                WebkitBackdropFilter: 'blur(20px) saturate(180%)',
              }}>
                <div className={`w-2 h-2 rounded-full ${
                  ollamaStatus === 'running' ? 'bg-emerald-500 shadow-lg shadow-emerald-500/50 animate-pulse' : 
                  ollamaStatus === 'checking' ? 'bg-amber-500 shadow-lg shadow-amber-500/50 animate-pulse' : 'bg-rose-500'
                }`} />
                <span className="text-xs font-medium text-slate-300">
                  {ollamaStatus === 'running' ? 'Connected' : 
                   ollamaStatus === 'checking' ? 'Checking...' : 'Offline'}
                </span>
              </div>
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
              onSelectModel={setSelectedModel}
              onToggleRouter={setUseRouter}
              apiUrl={API_URL}
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
