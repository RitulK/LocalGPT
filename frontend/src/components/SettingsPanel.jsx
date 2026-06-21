import { useEffect, useState } from 'react';
import { Brain, Code2, MessageCircle, RotateCcw, Save, SlidersHorizontal } from 'lucide-react';

const defaults = {
  default_general_model: '',
  default_coding_model: '',
  default_reasoning_model: '',
  router_enabled: true,
  router_models: []
};

export default function SettingsPanel({ settings, onUpdateSettings, models, apiUrl }) {
  const [activeTab, setActiveTab] = useState('router');
  const [localSettings, setLocalSettings] = useState({ ...defaults, ...settings });
  const [saved, setSaved] = useState(false);

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
    const firstModel = models[0]?.name || '';
    setLocalSettings({
      default_general_model: firstModel,
      default_coding_model: models.find((model) => model.name.toLowerCase().includes('coder'))?.name || firstModel,
      default_reasoning_model: firstModel,
      router_enabled: true,
      router_models: models.map((model) => model.name)
    });
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
              Configure the router models and default model roles used by LocalGPT.
            </p>
          </div>
        </div>

        <div className="grid gap-5 lg:grid-cols-[220px_1fr]">
          <div className="space-y-3 rounded-3xl border border-white/[0.08] bg-[#07100f]/72 p-4 shadow-[0_24px_70px_rgba(0,0,0,0.18)] backdrop-blur-xl">
            <TabButton
              label="Router models"
              active={activeTab === 'router'}
              onClick={() => setActiveTab('router')}
            />
            <TabButton
              label="Default roles"
              active={activeTab === 'roles'}
              onClick={() => setActiveTab('roles')}
            />
          </div>

          <div className="space-y-5">
            {activeTab === 'router' ? (
              <section className="rounded-3xl border border-white/[0.08] bg-[#07100f]/72 p-6 shadow-[0_24px_70px_rgba(0,0,0,0.18)] backdrop-blur-xl">
                <div className="mb-5 flex items-center justify-between gap-4">
                  <div>
                    <h3 className="text-lg font-semibold text-white">Router model list</h3>
                    <p className="mt-1 text-sm text-[#819690]">Select which installed models the router may use.</p>
                  </div>
                  <button
                    onClick={() => setLocalSettings({
                      ...localSettings,
                      router_models: models.map((model) => model.name)
                    })}
                    className="rounded-2xl border border-white/[0.08] bg-white/[0.04] px-4 py-2 text-sm text-[#cbdad6] transition hover:border-[#28ead8]/25 hover:text-[#8ffcf0]"
                  >
                    Select all
                  </button>
                </div>

                <div className="grid gap-3">
                  {models.length === 0 ? (
                    <div className="rounded-2xl border border-white/[0.08] bg-[#0b1716] p-4 text-sm text-[#819690]">No local models found.</div>
                  ) : (
                    models.map((model) => (
                      <label
                        key={model.name}
                        className="flex cursor-pointer items-center rounded-2xl border border-white/[0.08] bg-[#0b1716] px-4 py-3 text-sm transition hover:border-[#28ead8]/25"
                      >
                        <input
                          type="checkbox"
                          checked={localSettings.router_models?.includes(model.name) || false}
                          onChange={(e) => {
                            const selected = new Set(localSettings.router_models || []);
                            if (e.target.checked) {
                              selected.add(model.name);
                            } else {
                              selected.delete(model.name);
                            }
                            setLocalSettings({
                              ...localSettings,
                              router_models: Array.from(selected)
                            });
                          }}
                          className="mr-3 h-4 w-4 rounded border-white/[0.15] bg-transparent text-[#20dcca] focus:ring-[#20dcca]"
                        />
                        <span className="truncate">{model.name}</span>
                      </label>
                    ))
                  )}
                </div>
              </section>
            ) : (
              <section className="rounded-3xl border border-white/[0.08] bg-[#07100f]/72 p-6 shadow-[0_24px_70px_rgba(0,0,0,0.18)] backdrop-blur-xl">
                <h3 className="text-lg font-semibold text-white">Default model roles</h3>
                <p className="mt-1 text-sm text-[#819690]">Choose which installed models should be preferred by each route.</p>

                <div className="mt-5 grid gap-4">
                  <ModelSelect
                    label="General conversations"
                    value={localSettings.default_general_model || ''}
                    models={models}
                    onChange={(value) => setLocalSettings({ ...localSettings, default_general_model: value })}
                  />
                  <ModelSelect
                    label="Coding and debugging"
                    value={localSettings.default_coding_model || ''}
                    models={models}
                    onChange={(value) => setLocalSettings({ ...localSettings, default_coding_model: value })}
                  />
                  <ModelSelect
                    label="Reasoning and analysis"
                    value={localSettings.default_reasoning_model || ''}
                    models={models}
                    onChange={(value) => setLocalSettings({ ...localSettings, default_reasoning_model: value })}
                  />
                </div>
              </section>
            )}

            <div className="rounded-3xl border border-white/[0.08] bg-[#07100f]/72 p-6 shadow-[0_24px_70px_rgba(0,0,0,0.18)] backdrop-blur-xl">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-white">Save settings</h3>
                  <p className="mt-1 text-sm text-[#819690]">Persist your router model list and default model role preferences.</p>
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
      </div>
    </main>
  );
}

function TabButton({ label, active, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`w-full rounded-2xl px-4 py-3 text-left text-sm font-semibold transition ${
        active
          ? 'border border-[#28ead8]/20 bg-[#20dcca]/10 text-[#e7fff8]'
          : 'border border-white/[0.08] bg-[#07100f]/70 text-[#8da19c] hover:border-[#28ead8]/15 hover:bg-[#0f1e1c] hover:text-[#edf7f4]'
      }`}
    >
      {label}
    </button>
  );
}

function ModelSelect({ label, value, models, onChange }) {
  return (
    <label className="block">
      <span className="mb-2 block text-sm font-medium text-[#dce9e5]">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="h-12 w-full rounded-2xl border border-white/[0.08] bg-[#0b1716] px-4 text-sm text-white outline-none transition focus:border-[#28ead8]/35"
      >
        <option value="">Select a model</option>
        {models.map((model) => (
          <option key={model.name} value={model.name}>
            {model.name}
          </option>
        ))}
      </select>
    </label>
  );
}
