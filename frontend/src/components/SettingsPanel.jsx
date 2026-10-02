import { useEffect, useState } from 'react';
import { Brain, RotateCcw, Save, SlidersHorizontal, Sparkles } from 'lucide-react';

const defaults = {
  enable_thinking: false,
  reasoning_budget: 8192
};

export default function SettingsPanel({ settings, onUpdateSettings, apiUrl }) {
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
    setLocalSettings({ ...defaults });
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
              Configure model inference and workspace parameters for LocalGPT.
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
