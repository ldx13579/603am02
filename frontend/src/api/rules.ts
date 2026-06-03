import client from './client';

export interface RuleConfig {
  enabled: boolean;
  max_files_per_commit: number;
  min_message_length: number;
  max_lines_changed: number;
  dingtalk_webhook_url: boolean;
  dingtalk_silence_minutes: number;
  collaboration_max_nodes: number;
}

export async function getRuleConfig(): Promise<RuleConfig> {
  const { data } = await client.get('/violations/rules/config');
  return data;
}

export async function updateRuleConfig(config: Partial<RuleConfig>): Promise<RuleConfig> {
  const { data } = await client.put('/violations/rules/config', config);
  return data;
}
