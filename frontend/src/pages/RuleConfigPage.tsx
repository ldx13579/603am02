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
        collaboration_max_nodes: config.collaboration_max_nodes,
      });
      setConfig(updated);
      setMessage('Configuration saved successfully');
    } catch {
      setMessage('Failed to save configuration');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="loading">Loading configuration...</div>;
  if (!config) return <div className="error">Unable to load configuration</div>;

  return (
    <div className="rule-config-page">
      <div className="report-header">
        <h1>System Configuration</h1>
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

      <div className="chart-section" style={{ maxWidth: 640 }}>
        <h2>Rule Engine</h2>
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
          <p style={hintStyle}>Commits touching more files than this will be flagged as violations</p>
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
          <label style={labelStyle}>Max Lines Changed Per Commit</label>
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

        <h2>Collaboration Network</h2>

        <div style={fieldStyle}>
          <label style={labelStyle}>Max Display Nodes</label>
          <input
            type="number"
            min={5}
            max={200}
            value={config.collaboration_max_nodes}
            onChange={(e) => setConfig({ ...config, collaboration_max_nodes: parseInt(e.target.value) || 50 })}
            style={inputStyle}
          />
          <p style={hintStyle}>
            Maximum number of developer nodes shown in the collaboration graph.
            Excess nodes are collapsed into a cluster to prevent rendering performance issues.
          </p>
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
          <p style={hintStyle}>Set DINGTALK_WEBHOOK_URL environment variable to enable alerts</p>
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
          <p style={hintStyle}>
            Same repository will not be alerted again within this time window.
            Set to 0 to disable silence (alert on every scan).
          </p>
        </div>

        <div style={{ marginTop: 28, display: 'flex', gap: 12 }}>
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
          <button
            onClick={() => {
              getRuleConfig().then(setConfig).catch(() => {});
              setMessage(null);
            }}
            style={{
              padding: '10px 24px',
              borderRadius: 6,
              border: '1px solid #ddd',
              background: '#fff',
              color: '#333',
              fontSize: 14,
              cursor: 'pointer',
            }}
          >
            Reset
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
