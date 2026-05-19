import { useState, useEffect } from 'react';
import { Save, RotateCcw } from 'lucide-react';

export default function SettingsPanel({ settings, onUpdateSettings, models }) {
  const [localSettings, setLocalSettings] = useState(settings);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    setLocalSettings(settings);
  }, [settings]);

  const handleSave = async () => {
    try {
      const response = await fetch('http://localhost:8000/settings', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(localSettings),
      });

      if (response.ok) {
        onUpdateSettings(localSettings);
        setSaved(true);
        setTimeout(() => setSaved(false), 2000);
      }
    } catch (error) {
      console.error('Failed to save settings:', error);
    }
  };

  const handleReset = () => {
    const defaults = {
      default_general_model: 'llama3.2:latest',
      default_coding_model: 'qwen2.5-coder:latest',
      default_reasoning_model: 'llama3.2:latest',
      router_enabled: true
    };
    setLocalSettings(defaults);
  };

  return (
    <div className="flex-1 overflow-y-auto p-8 bg-gradient-to-br from-slate-950/50 to-slate-900/50">
      <div className="max-w-3xl mx-auto">
        <h2 className="text-2xl font-bold mb-6 text-gray-100">Settings</h2>

        <div className="space-y-6">
          {/* Router Settings */}
          <div className="bg-white/5 backdrop-blur-md rounded-lg p-6 border border-white/10 shadow-lg">
            <h3 className="text-lg font-semibold mb-4 text-gray-100">Router Configuration</h3>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium text-gray-300">
                    Enable Router Mode
                  </label>
                  <p className="text-xs text-gray-500 mt-1">
                    Automatically select the best model based on prompt analysis
                  </p>
                </div>
                <button
                  onClick={() => setLocalSettings({
                    ...localSettings,
                    router_enabled: !localSettings.router_enabled
                  })}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    localSettings.router_enabled ? 'bg-indigo-600' : 'bg-slate-600'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      localSettings.router_enabled ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>
            </div>
          </div>

          {/* Model Preferences */}
          <div className="bg-white/5 backdrop-blur-md rounded-lg p-6 border border-white/10 shadow-lg">
            <h3 className="text-lg font-semibold mb-4 text-gray-100">Default Models</h3>
            <p className="text-sm text-gray-400 mb-6">
              Select which models the router should use for different types of tasks
            </p>

            <div className="space-y-4">
              {/* General Model */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  General Conversations
                </label>
                <select
                  value={localSettings.default_general_model || ''}
                  onChange={(e) => setLocalSettings({
                    ...localSettings,
                    default_general_model: e.target.value
                  })}
                  className="w-full bg-white/5 backdrop-blur-md text-gray-100 rounded-lg px-3 py-2 text-sm border border-white/10 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="">Select a model</option>
                  {models.map((model) => (
                    <option key={model.name} value={model.name}>
                      {model.name}
                    </option>
                  ))}
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  Used for everyday conversations and quick questions
                </p>
              </div>

              {/* Coding Model */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Coding & Development
                </label>
                <select
                  value={localSettings.default_coding_model || ''}
                  onChange={(e) => setLocalSettings({
                    ...localSettings,
                    default_coding_model: e.target.value
                  })}
                  className="w-full bg-white/5 backdrop-blur-md text-gray-100 rounded-lg px-3 py-2 text-sm border border-white/10 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="">Select a model</option>
                  {models.map((model) => (
                    <option key={model.name} value={model.name}>
                      {model.name}
                    </option>
                  ))}
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  Used when code-related keywords are detected
                </p>
              </div>

              {/* Reasoning Model */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Reasoning & Analysis
                </label>
                <select
                  value={localSettings.default_reasoning_model || ''}
                  onChange={(e) => setLocalSettings({
                    ...localSettings,
                    default_reasoning_model: e.target.value
                  })}
                  className="w-full bg-white/5 backdrop-blur-md text-gray-100 rounded-lg px-3 py-2 text-sm border border-white/10 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="">Select a model</option>
                  {models.map((model) => (
                    <option key={model.name} value={model.name}>
                      {model.name}
                    </option>
                  ))}
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  Used for analytical tasks and complex reasoning
                </p>
              </div>
            </div>
          </div>

          {/* Router Logic Info */}
          <div className="bg-indigo-500/10 border border-indigo-500/30 rounded-lg p-6 backdrop-blur-md">
            <h3 className="text-lg font-semibold mb-3 text-indigo-400">How Router Mode Works</h3>
            <ul className="space-y-2 text-sm text-gray-300">
              <li className="flex items-start gap-2">
                <span className="text-indigo-400 mt-1">•</span>
                <span>Detects coding keywords (code, function, debug, etc.) → Uses Coding Model</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-indigo-400 mt-1">•</span>
                <span>Detects reasoning keywords (analyze, compare, why, etc.) → Uses Reasoning Model</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-indigo-400 mt-1">•</span>
                <span>Detects code blocks in prompt → Uses Coding Model</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-indigo-400 mt-1">•</span>
                <span>Long prompts (100+ words) → Uses Reasoning Model</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-indigo-400 mt-1">•</span>
                <span>Default → Uses General Model</span>
              </li>
            </ul>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3">
            <button
              onClick={handleSave}
              className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white rounded-lg transition font-medium shadow-lg shadow-indigo-500/30 backdrop-blur-sm"
            >
              <Save className="w-4 h-4" />
              {saved ? 'Saved!' : 'Save Settings'}
            </button>
            <button
              onClick={handleReset}
              className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 text-gray-300 rounded-lg transition border border-white/10 backdrop-blur-md"
            >
              <RotateCcw className="w-4 h-4" />
              Reset to Defaults
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
