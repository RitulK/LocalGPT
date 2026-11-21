import { useEffect, useState } from 'react';
import { Brain, FolderSync, RotateCcw, Save, SlidersHorizontal, Sparkles } from 'lucide-react';

const defaults = {
  enable_thinking: false,
  reasoning_budget: 8192,
  obsidian_api_address: 'https://127.0.0.1:27124',
  obsidian_api_key: '',
  obsidian_verify_tls: true,
  obsidian_ca_path: '',
  obsidian_allowed_folder: 'BuddyAI/',
  obsidian_display_name: '',
  obsidian_allow_read: true,
  obsidian_allow_write: true,
  obsidian_allow_delete: false
};

export default function SettingsPanel({ settings, onUpdateSettings, apiUrl }) {
  const [localSettings, setLocalSettings] = useState({ ...defaults, ...settings });
  const [saved, setSaved] = useState(false);
  const [obsidianStatus, setObsidianStatus] = useState('idle');
  const [obsidianMessage, setObsidianMessage] = useState('');

  useEffect(() => {
    setLocalSettings({ ...defaults, ...settings });
  }, [settings]);

  const handleSave = async () => {
    try {
      const response = await fetch(`${apiUrl}/settings`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(localSettings)
      });

      if (response.ok) {
        const data = await response.json();
        onUpdateSettings(data.settings || localSettings);
        setSaved(true);
        setTimeout(() => setSaved(false), 1800);
      }
    } catch (error) {
      console.error('Failed to save settings:', error);
    }
  };

  const handleReset = () => {
    setLocalSettings({ ...defaults });
  };

  const testObsidian = async () => {
    setObsidianStatus('checking');
    setObsidianMessage('');
    try {
      const response = await fetch(`${apiUrl}/obsidian/test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          api_address: localSettings.obsidian_api_address,
          api_key: localSettings.obsidian_api_key,
          verify_tls: localSettings.obsidian_verify_tls,
          ca_path: localSettings.obsidian_ca_path
        })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Connection failed');
      setObsidianStatus(data.connected ? 'connected' : 'error');
      setObsidianMessage(data.connected
        ? `Connected${localSettings.obsidian_display_name ? ` to ${localSettings.obsidian_display_name}` : ''}`
        : 'The API key was not accepted');
    } catch (error) {
      setObsidianStatus('error');
      setObsidianMessage(error.message);
    }
  };

  return (
    <main className="h-full overflow-y-auto px-8 py-7">
      <div className="mx-auto max-w-5xl">
        <div className="mb-8 flex flex-col gap-4">
          <div className="inline-flex items-center gap-2 rounded-full border border-[#28ead8]/20 bg-[#20dcca]/10 px-3 py-1.5 text-xs text-[#8ffcf0]">
            <SlidersHorizontal className="h-3.5 w-3.5" />
            Workspace preferences
          </div>
          <div>
            <h2 className="text-4xl font-semibold tracking-[-0.03em] text-white">Settings</h2>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-[#8da19c]">
              Configure model inference and workspace parameters for Buddyai.
            </p>
          </div>
        </div>

        <div className="space-y-6">
          <section className="rounded-3xl border border-white/[0.08] bg-[#07100f]/72 p-6 shadow-[0_24px_70px_rgba(0,0,0,0.18)] backdrop-blur-xl">
            <div className="mb-6 flex items-center gap-3">
              <div className="grid h-10 w-10 place-items-center rounded-xl border border-[#28ead8]/25 bg-[#20dcca]/10 text-[#72fff0]">
                <Brain className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-white">Reasoning & Inference</h3>
                <p className="text-sm text-[#819690]">Control reasoning tokens and thinking output behavior</p>
              </div>
            </div>

            <div className="space-y-5">
              <label className="flex cursor-pointer items-start justify-between rounded-2xl border border-white/[0.08] bg-[#0b1716] p-4 transition hover:border-[#28ead8]/25">
                <div className="pr-4">
                  <div className="text-sm font-medium text-white">Enable reasoning thoughts</div>
                  <div className="mt-1 text-xs leading-5 text-[#819690]">
                    Show thinking traces for models supporting reasoning outputs (e.g. DeepSeek-R1 or Nemotron).
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={Boolean(localSettings.enable_thinking)}
                  onChange={(e) =>
                    setLocalSettings({ ...localSettings, enable_thinking: e.target.checked })
                  }
                  className="mt-1 h-5 w-5 rounded border-white/[0.15] bg-transparent text-[#20dcca] focus:ring-[#20dcca]"
                />
              </label>

              <div className="rounded-2xl border border-white/[0.08] bg-[#0b1716] p-4">
                <label className="block text-sm font-medium text-white">
                  Reasoning budget (max tokens)
                </label>
                <div className="mt-1 text-xs text-[#819690]">
                  Maximum token limit allocated for the internal reasoning phase before response generation.
                </div>
                <div className="mt-3 flex items-center gap-4">
                  <input
                    type="range"
                    min="1024"
                    max="32768"
                    step="1024"
                    value={localSettings.reasoning_budget || 8192}
                    onChange={(e) =>
                      setLocalSettings({
                        ...localSettings,
                        reasoning_budget: parseInt(e.target.value, 10)
                      })
                    }
                    className="h-2 flex-1 cursor-pointer appearance-none rounded-lg bg-white/[0.1] accent-[#20dcca]"
                  />
                  <span className="min-w-[70px] text-right font-mono text-sm text-[#72fff0]">
                    {localSettings.reasoning_budget || 8192}
                  </span>
                </div>
              </div>
            </div>
          </section>

          <section className="rounded-3xl border border-white/[0.08] bg-[#07100f]/72 p-6 shadow-[0_24px_70px_rgba(0,0,0,0.18)] backdrop-blur-xl">
            <div className="mb-6 flex items-center gap-3">
              <div className="grid h-10 w-10 place-items-center rounded-xl border border-[#28ead8]/25 bg-[#20dcca]/10 text-[#72fff0]">
                <FolderSync className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-white">Obsidian</h3>
                <p className="text-sm text-[#819690]">Connect to the Local REST API with MCP plugin</p>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <label className="text-sm text-[#b9c9c5]">
                API address
                <input
                  value={localSettings.obsidian_api_address}
                  onChange={(e) => setLocalSettings({ ...localSettings, obsidian_api_address: e.target.value })}
                  className="mt-2 w-full rounded-xl border border-white/[0.08] bg-[#0b1716] px-3 py-2.5 text-sm text-white outline-none focus:border-[#28ead8]/35"
                  placeholder="https://127.0.0.1:27124"
                />
              </label>
              <label className="text-sm text-[#b9c9c5]">
                API key
                <input
                  type="password"
                  value={localSettings.obsidian_api_key}
                  onChange={(e) => setLocalSettings({ ...localSettings, obsidian_api_key: e.target.value })}
                  className="mt-2 w-full rounded-xl border border-white/[0.08] bg-[#0b1716] px-3 py-2.5 text-sm text-white outline-none focus:border-[#28ead8]/35"
                  placeholder="Paste the plugin API key"
                />
              </label>
              <label className="text-sm text-[#b9c9c5]">
                Certificate authority path
                <input
                  value={localSettings.obsidian_ca_path}
                  onChange={(e) => setLocalSettings({ ...localSettings, obsidian_ca_path: e.target.value })}
                  className="mt-2 w-full rounded-xl border border-white/[0.08] bg-[#0b1716] px-3 py-2.5 text-sm text-white outline-none focus:border-[#28ead8]/35"
                  placeholder="/path/to/obsidian-local-rest-api.crt"
                />
              </label>
              <label className="text-sm text-[#b9c9c5]">
                Allowed write folder
                <input
                  value={localSettings.obsidian_allowed_folder}
                  onChange={(e) => setLocalSettings({ ...localSettings, obsidian_allowed_folder: e.target.value })}
                  className="mt-2 w-full rounded-xl border border-white/[0.08] bg-[#0b1716] px-3 py-2.5 text-sm text-white outline-none focus:border-[#28ead8]/35"
                  placeholder="BuddyAI/"
                />
              </label>
              <label className="text-sm text-[#b9c9c5]">
                Vault display name
                <input
                  value={localSettings.obsidian_display_name}
                  onChange={(e) => setLocalSettings({ ...localSettings, obsidian_display_name: e.target.value })}
                  className="mt-2 w-full rounded-xl border border-white/[0.08] bg-[#0b1716] px-3 py-2.5 text-sm text-white outline-none focus:border-[#28ead8]/35"
                  placeholder="My vault"
                />
              </label>
              <label className="mt-6 flex items-center gap-3 text-sm text-[#b9c9c5]">
                <input
                  type="checkbox"
                  checked={Boolean(localSettings.obsidian_verify_tls)}
                  onChange={(e) => setLocalSettings({ ...localSettings, obsidian_verify_tls: e.target.checked })}
                  className="h-4 w-4 accent-[#20dcca]"
                />
                Verify HTTPS certificate
              </label>
            </div>

            <div className="mt-5 grid gap-3 md:grid-cols-3">
              {[
                ['obsidian_allow_read', 'Search and read'],
                ['obsidian_allow_write', 'Create and edit'],
                ['obsidian_allow_delete', 'Delete (separate confirmation)']
              ].map(([field, label]) => (
                <label key={field} className="flex items-center gap-3 rounded-xl border border-white/[0.07] bg-[#0b1716] px-3 py-3 text-sm text-[#b9c9c5]">
                  <input
                    type="checkbox"
                    checked={Boolean(localSettings[field])}
                    onChange={(e) => setLocalSettings({ ...localSettings, [field]: e.target.checked })}
                    className="h-4 w-4 accent-[#20dcca]"
                  />
                  {label}
                </label>
              ))}
            </div>

            <div className="mt-5 flex flex-wrap items-center gap-3">
              <button
                type="button"
                onClick={testObsidian}
                className="rounded-xl border border-[#28ead8]/20 bg-[#20dcca]/10 px-4 py-2.5 text-sm font-semibold text-[#8ffcf0] transition hover:bg-[#20dcca]/16"
              >
                {obsidianStatus === 'checking' ? 'Checking...' : 'Test connection'}
              </button>
              {obsidianMessage && (
                <span className={`text-sm ${obsidianStatus === 'connected' ? 'text-emerald-300' : 'text-rose-300'}`}>
                  {obsidianMessage}
                </span>
              )}
            </div>
          </section>

          <div className="rounded-3xl border border-white/[0.08] bg-[#07100f]/72 p-6 shadow-[0_24px_70px_rgba(0,0,0,0.18)] backdrop-blur-xl">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h3 className="text-lg font-semibold text-white">Save settings</h3>
                <p className="mt-1 text-sm text-[#819690]">Persist your workspace configuration locally.</p>
              </div>
              <div className="flex flex-wrap gap-3">
                <button
                  onClick={handleSave}
                  className="inline-flex items-center justify-center gap-2 rounded-2xl bg-[#20dcca] px-4 py-3 text-sm font-semibold text-[#06211e] shadow-[0_18px_45px_rgba(32,220,202,0.18)] transition hover:bg-[#68f8ea]"
                >
                  <Save className="h-4 w-4" />
                  {saved ? 'Saved' : 'Save settings'}
                </button>
                <button
                  onClick={handleReset}
                  className="inline-flex items-center justify-center gap-2 rounded-2xl border border-white/[0.08] bg-white/[0.035] px-4 py-3 text-sm font-semibold text-[#cbdad6] transition hover:border-[#28ead8]/25 hover:text-[#8ffcf0]"
                >
                  <RotateCcw className="h-4 w-4" />
                  Reset defaults
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
