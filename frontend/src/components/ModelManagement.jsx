import { useState } from 'react';
import { RefreshCw, Database, HardDrive, Calendar, CheckCircle } from 'lucide-react';

export default function ModelManagement({ models, onRefresh, selectedModel }) {
  const [refreshing, setRefreshing] = useState(false);

  const handleRefresh = async () => {
    setRefreshing(true);
    await onRefresh();
    setTimeout(() => setRefreshing(false), 500);
  };

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };

  return (
    <div className="flex-1 overflow-y-auto p-8 bg-gradient-to-br from-slate-950/50 to-slate-900/50">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-100">Model Management</h2>
            <p className="text-sm text-gray-400 mt-1">
              Manage your locally installed Ollama models
            </p>
          </div>
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 disabled:from-slate-700 disabled:to-slate-700 text-white rounded-lg transition font-medium shadow-lg shadow-indigo-500/30 backdrop-blur-sm"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="bg-white/5 backdrop-blur-md rounded-lg p-4 border border-white/10 shadow-lg">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-indigo-600/20 rounded-lg backdrop-blur-sm">
                <Database className="w-5 h-5 text-indigo-400" />
              </div>
              <div>
                <div className="text-2xl font-bold text-gray-100">{models.length}</div>
                <div className="text-sm text-gray-400">Total Models</div>
              </div>
            </div>
          </div>

          <div className="bg-white/5 backdrop-blur-md rounded-lg p-4 border border-white/10 shadow-lg">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-emerald-600/20 rounded-lg backdrop-blur-sm">
                <CheckCircle className="w-5 h-5 text-emerald-400" />
              </div>
              <div>
                <div className="text-2xl font-bold text-gray-100">
                  {models.length}
                </div>
                <div className="text-sm text-gray-400">Available Models</div>
              </div>
            </div>
          </div>

          <div className="bg-white/5 backdrop-blur-md rounded-lg p-4 border border-white/10 shadow-lg">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-600/20 rounded-lg backdrop-blur-sm">
                <HardDrive className="w-5 h-5 text-purple-400" />
              </div>
              <div>
                <div className="text-2xl font-bold text-gray-100">
                  {formatBytes(models.reduce((acc, m) => acc + (m.size || 0), 0))}
                </div>
                <div className="text-sm text-gray-400">Total Size</div>
              </div>
            </div>
          </div>
        </div>

        {/* Models List */}
        {models.length === 0 ? (
          <div className="bg-white/5 backdrop-blur-md rounded-lg p-12 border border-white/10 text-center shadow-lg">
            <Database className="w-16 h-16 text-gray-600 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-300 mb-2">No Models Found</h3>
            <p className="text-gray-500 mb-4">
              No Ollama models are currently installed on your system.
            </p>
            <div className="bg-white/5 backdrop-blur-sm rounded-lg p-4 max-w-md mx-auto text-left border border-white/10">
              <p className="text-sm text-gray-400 mb-2">To install a model, run:</p>
              <code className="block bg-slate-950/50 text-emerald-400 px-3 py-2 rounded font-mono text-sm border border-white/5">
                ollama pull llama3.2
              </code>
              <p className="text-xs text-gray-500 mt-2">
                Or visit: <a href="https://ollama.com/library" target="_blank" rel="noopener noreferrer" className="text-indigo-400 hover:underline">ollama.com/library</a>
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            {models.map((model) => {
              const isSelected = selectedModel === model.name;
              
              return (
                <div
                  key={model.name}
                  className={`bg-white/5 backdrop-blur-md rounded-lg p-5 border transition shadow-lg ${
                    isSelected
                      ? 'border-indigo-500/50 bg-indigo-500/10'
                      : 'border-white/10 hover:border-white/20'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-semibold text-gray-100">
                          {model.name}
                        </h3>
                        {isSelected && (
                          <span className="px-2 py-1 bg-blue-600 text-white text-xs rounded-full font-medium">
                            Selected
                          </span>
                        )}
                      </div>

                      <div className="grid grid-cols-3 gap-4 text-sm">
                        <div>
                          <div className="text-gray-500 mb-1">Size</div>
                          <div className="text-gray-300 font-medium">
                            {formatBytes(model.size)}
                          </div>
                        </div>
                        <div>
                          <div className="text-gray-500 mb-1">Last Modified</div>
                          <div className="text-gray-300 font-medium">
                            {formatDate(model.modified_at)}
                          </div>
                        </div>
                        <div>
                          <div className="text-gray-500 mb-1">Status</div>
                          <div className="flex items-center gap-2">
                            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                            <span className="text-gray-300 font-medium">Available</span>
                          </div>
                        </div>
                      </div>

                      {model.digest && (
                        <div className="mt-3 pt-3 border-t border-gray-700">
                          <div className="text-xs text-gray-500">
                            Digest: <code className="text-gray-400 font-mono">{model.digest.slice(0, 32)}...</code>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Info Box */}
        <div className="mt-6 bg-gray-800 border border-gray-700 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-gray-300 mb-2">💡 Tips</h3>
          <ul className="space-y-1 text-sm text-gray-400">
            <li>• To install a new model: <code className="bg-gray-900 px-2 py-0.5 rounded text-blue-400">ollama pull model-name</code></li>
            <li>• To remove a model: <code className="bg-gray-900 px-2 py-0.5 rounded text-blue-400">ollama rm model-name</code></li>
            <li>• To list all models: <code className="bg-gray-900 px-2 py-0.5 rounded text-blue-400">ollama list</code></li>
            <li>• Models are automatically detected from your Ollama installation</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
