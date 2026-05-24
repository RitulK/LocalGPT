import { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import ChatWindow from './components/ChatWindow';
import ModelManagement from './components/ModelManagement';
import SettingsPanel from './components/SettingsPanel';

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
  const [activeTab, setActiveTab] = useState('chat'); // chat, models, settings
  const [ollamaStatus, setOllamaStatus] = useState('checking');
  const [settings, setSettings] = useState({
    default_general_model: null,
    default_coding_model: null,
    default_reasoning_model: null,
    router_enabled: true
  });

  const currentConversation = conversations.find(c => c.id === currentConversationId);

  // Fetch models on mount
  useEffect(() => {
    fetchConversations();
    fetchModels();
    fetchSettings();
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

  const fetchSettings = async () => {
    try {
      const response = await fetch(`${API_URL}/settings`);
      const data = await response.json();
      setSettings(data);
      setUseRouter(data.router_enabled ?? true);
    } catch (error) {
      console.error('Failed to fetch settings:', error);
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
    <div className="h-screen w-screen overflow-hidden bg-[#050706] text-[#e8f1ef]">
      <div className="app-shell relative flex h-full w-full overflow-hidden">
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
        <div className="relative z-10 flex-1 flex flex-col overflow-hidden w-full">
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
              onSelectModel={setSelectedModel}
            />
          )}

          {activeTab === 'settings' && (
            <SettingsPanel
              settings={settings}
              onUpdateSettings={(updatedSettings) => {
                setSettings(updatedSettings);
                setUseRouter(updatedSettings.router_enabled ?? true);
              }}
              models={models}
              apiUrl={API_URL}
            />
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
