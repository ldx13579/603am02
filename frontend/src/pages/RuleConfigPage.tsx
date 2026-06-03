import { useState, useEffect } from 'react';
import { getRuleConfig, updateRuleConfig, type RuleConfig } from '../api/rules';

export default function RuleConfigPage() {
  const [config, setConfig] = useState<RuleConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    getRuleConfig()
      .then(setConfig)
      .catch(() => setMessage('Failed to load rule config'))
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async () => {
    if (!config) return;
    setSaving(true);
    setMessage(null);
    try {
      const updated = await updateRuleConfig({
        enabled: config.enabled,
        max_files_per_commit: config.max_files_per_commit,
        min_message_length: config.min_message_length,
        max_lines_changed: config.max_lines_changed,
        dingtalk_silence_minutes: config.dingtalk_silence_minutes,
      });
      setConfig(updated);
      setMessage('Rules saved successfully');
    } catch {
      setMessage('Failed to save rules');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="loading">Loading rule config...</div>;
  if (!config) return <div className="error">Unable to load rule configuration</div>;

  return (
    <div className="rule-config-page">
      <div className="report-header">
        <h1>Rule Configuration</h1>
      </div>

      {message && (
        <div style={{
          padding: '10px 16px',
          marginBottom: 16,
          borderRadius: 6,
          background: message.includes('success') ? '#D4EDDA' : '#F8D7DA',
          color: message.includes('success') ? '#155724' : '#721C24',
          fontSize: 14,
        }}>
          {message}
        </div>
      )}

      <div className="chart-section" style={{ maxWidth: 600 }}>
        <h2>General</h2>
        <div style={{ marginBottom: 20 }}>
          <label style={labelStyle}>
            <input
              type="checkbox"
              checked={config.enabled}
              onChange={(e) => setConfig({ ...config, enabled: e.target.checked })}
              style={{ marginRight: 8 }}
            />
            Rule Engine Enabled
          </label>
          <p style={hintStyle}>Enable or disable all rule checks during analysis</p>
        </div>

        <h2>Rule Thresholds</h2>

        <div style={fieldStyle}>
          <label style={labelStyle}>Max Files Per Commit</label>
          <input
            type="number"
            min={1}
            max={200}
            value={config.max_files_per_commit}
            onChange={(e) => setConfig({ ...config, max_files_per_commit: parseInt(e.target.value) || 20 })}
            style={inputStyle}
          />
          <p style={hintStyle}>Commits touching more files than this threshold will be flagged</p>
        </div>

        <div style={fieldStyle}>
          <label style={labelStyle}>Min Commit Message Length</label>
          <input
            type="number"
            min={0}
            max={100}
            value={config.min_message_length}
            onChange={(e) => setConfig({ ...config, min_message_length: parseInt(e.target.value) || 5 })}
            style={inputStyle}
          />
          <p style={hintStyle}>Commits with messages shorter than this will be flagged</p>
        </div>

        <div style={fieldStyle}>
          <label style={labelStyle}>Max Lines Changed</label>
          <input
            type="number"
            min={100}
            max={100000}
            step={100}
            value={config.max_lines_changed}
            onChange={(e) => setConfig({ ...config, max_lines_changed: parseInt(e.target.value) || 1000 })}
            style={inputStyle}
          />
          <p style={hintStyle}>Commits with total insertions + deletions exceeding this will be flagged</p>
        </div>

        <h2>DingTalk Alert</h2>

        <div style={fieldStyle}>
          <label style={labelStyle}>
            Webhook Status:
            <span style={{
              marginLeft: 8,
              padding: '2px 8px',
              borderRadius: 8,
              fontSize: 12,
              background: config.dingtalk_webhook_url ? '#D4EDDA' : '#F8D7DA',
              color: config.dingtalk_webhook_url ? '#155724' : '#721C24',
            }}>
              {config.dingtalk_webhook_url ? 'Configured' : 'Not configured'}
            </span>
          </label>
          <p style={hintStyle}>Set DINGTALK_WEBHOOK_URL in .env to enable alerts</p>
        </div>

        <div style={fieldStyle}>
          <label style={labelStyle}>Alert Silence Window (minutes)</label>
          <input
            type="number"
            min={0}
            max={1440}
            value={config.dingtalk_silence_minutes}
            onChange={(e) => setConfig({ ...config, dingtalk_silence_minutes: parseInt(e.target.value) || 60 })}
            style={inputStyle}
          />
          <p style={hintStyle}>Same repository alerts will be suppressed within this time window (0 = no silence)</p>
        </div>

        <div style={{ marginTop: 24 }}>
          <button
            onClick={handleSave}
            disabled={saving}
            style={{
              padding: '10px 24px',
              borderRadius: 6,
              border: 'none',
              background: saving ? '#ccc' : '#4A90D9',
              color: '#fff',
              fontSize: 14,
              cursor: saving ? 'not-allowed' : 'pointer',
            }}
          >
            {saving ? 'Saving...' : 'Save Configuration'}
          </button>
        </div>
      </div>
    </div>
  );
}

const labelStyle: React.CSSProperties = {
  fontSize: 14,
  fontWeight: 500,
  display: 'flex',
  alignItems: 'center',
};

const hintStyle: React.CSSProperties = {
  fontSize: 12,
  color: '#999',
  marginTop: 4,
  marginBottom: 0,
};

const fieldStyle: React.CSSProperties = {
  marginBottom: 20,
};

const inputStyle: React.CSSProperties = {
  display: 'block',
  marginTop: 6,
  padding: '8px 12px',
  borderRadius: 6,
  border: '1px solid #ddd',
  fontSize: 14,
  width: 200,
};
