export default {
  'GET:/setting/get_setting': () => ({
    code: 0, message: 'success',
    data: {
      default_count: 5,
      default_fetch_limit: 20,
      enabled_columns: [
        { value: 'one_minute_ai_office', label: '一分钟 AI 办公', enabled: true },
        { value: 'less_overtime', label: '今天少加班一小时', enabled: true },
        { value: 'boss_ai', label: '老板也能听懂的 AI', enabled: true },
        { value: 'ordinary_ai_toolbox', label: '普通人 AI 工具箱', enabled: false },
        { value: 'ai_pitfall_guide', label: 'AI 避坑指南', enabled: false },
      ],
      storage_type: 'local',
      model_provider: 'openai_compatible',
      model_key_masked: 'sk-****abcd',
    },
  }),

  'POST:/setting/update_setting': () => ({
    code: 0, message: 'success', data: true,
  }),
}
