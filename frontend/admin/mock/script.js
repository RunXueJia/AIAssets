const mockScript = {
  id: 'script_001',
  topic_id: 'topic_001',
  title: '用 AI 10 分钟写完一份周报',
  hook: '周五最痛苦的事，是发现周报还没写。',
  pain_point: '很多人一周做了不少事，但写周报时想不起来重点。',
  method: '先让 AI 整理工作记录，再生成周报结构。',
  steps: ['粘贴本周事项', '要求 AI 按成果、问题、下周计划整理', '人工补充关键数字'],
  example: '把会议纪要、待办记录和完成事项放到一起，让 AI 输出三段式周报。',
  summary: 'AI 负责整理，人负责判断，周报效率会高很多。',
  cta: '下次写周报前，先把本周记录丢给 AI 整理。',
  platform_title: '用 AI 10 分钟写完周报',
  description: '一个适合普通职场人的 AI 周报写作方法。',
  tags: ['AI办公', '职场效率', '周报'],
  cover_text: 'AI 写周报',
  pinned_comment: '试试先整理工作记录，再让 AI 生成周报结构。',
  status: 'pending_review',
  version: 1,
}

const mockStoryboards = [
  { id: 'shot_001', script_id: 'script_001', shot_no: 1, duration_seconds: 6, voiceover: '周五最痛苦的事，是发现周报还没写。', subtitle: '周报还没写？', visual_type: 'screen_recording', material_suggestion: '展示空白周报文档', motion_suggestion: '标题滑入' },
  { id: 'shot_002', script_id: 'script_001', shot_no: 2, duration_seconds: 8, voiceover: '你一周做了很多事，但写周报时却想不起来重点。', subtitle: '一周做了很多事但写不出来？', visual_type: 'screen_recording', material_suggestion: '展示零散的待办列表', motion_suggestion: '列表滚动' },
  { id: 'shot_003', script_id: 'script_001', shot_no: 3, duration_seconds: 15, voiceover: '先把工作记录整理好，再用 AI 生成周报结构，最后人工补充关键数字。', subtitle: 'AI 整理 + 人工补充', visual_type: 'screen_recording', material_suggestion: '展示 AI 生成过程', motion_suggestion: '分步展示' },
]

const mockSubtitles = [
  { id: 'sub_001', script_id: 'script_001', start_time: '00:00:00.000', end_time: '00:00:03.000', text: '周五最痛苦的事，是发现周报还没写。' },
  { id: 'sub_002', script_id: 'script_001', start_time: '00:00:03.000', end_time: '00:00:06.000', text: '你一周做了很多事，但写周报时却想不起来重点。' },
]

export default {
  'GET:/script/get_script_detail/{id}': (params, id) => ({
    code: 0, message: 'success',
    data: {
      script: mockScript,
      storyboards: mockStoryboards,
      subtitles: mockSubtitles,
      versions: [{ version: 1, operator_name: '系统生成', created_at: '2026-05-20 09:30:00' }],
    },
  }),

  'POST:/script/update_script': (data) => ({
    code: 0, message: 'success',
    data: { script_id: data.script_id, version: 2, updated_at: '2026-05-20 10:00:00' },
  }),

  'POST:/storyboard/update_storyboard': (data) => ({
    code: 0, message: 'success',
    data: { script_id: data.script_id, storyboard_count: (data.items || []).length, version: 2 },
  }),

  'POST:/subtitle/update_subtitle': (data) => ({
    code: 0, message: 'success',
    data: { script_id: data.script_id, subtitle_count: (data.items || []).length, version: 2 },
  }),
}
