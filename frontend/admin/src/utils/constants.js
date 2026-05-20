// Status enums mirroring backend constants.py — English values, Chinese labels

export const TASK_STATUS = {
  pending: '等待中',
  running: '运行中',
  success: '成功',
  failed: '失败',
  cancelled: '已取消',
  retrying: '重试中',
}

export const CONTENT_STATUS = {
  generating: '生成中',
  pending_review: '待审核',
  approved: '审核通过',
  approved_with_edit: '修改后通过',
  rejected: '驳回',
  regenerating: '重新生成中',
  pending_render: '待合成',
  rendering: '合成中',
  render_failed: '合成失败',
  rendered: '已合成',
  exported: '已导出',
  published: '已发布',
  offline: '已下线',
}

export const SOURCE_STATUS = {
  usable: '可用',
  not_suitable: '不适合',
  uncertain: '待确认',
}

export const MONITOR_STATUS = {
  enabled: '运行中',
  paused: '已暂停',
  deleted: '已删除',
}

export const GENERATION_TYPE = {
  topics_only: '只生成选题',
  topics_and_script: '生成选题和脚本',
  full_script_storyboard: '完整生成脚本和分镜',
}

export const STAGE_NAMES = {
  create_task: '正在创建任务',
  fetch_sources: '正在抓取相关内容',
  summarize_sources: '正在整理素材汇总',
  generate_topics: '正在生成选题',
  generate_script: '正在生成脚本',
  generate_storyboard: '正在生成分镜',
  generate_subtitle: '正在生成字幕',
  completed: '生成完成',
}

export const TOPIC_STATUS = {
  draft: '待确认',
  approved: '已通过',
  rejected: '已驳回',
  locked: '已锁定',
}

export const ROLES = {
  admin: '管理员',
  operation_manager: '运营负责人',
  content_editor: '内容编辑',
  video_operator: '视频运营',
  viewer: '只读查看者',
}

export const PLATFORMS = {
  douyin: '抖音',
  xiaohongshu: '小红书',
  bilibili: 'B 站',
  wechat_channels: '视频号',
  youtube_shorts: 'YouTube Shorts',
  tiktok: 'TikTok',
}

export const PUBLISH_STATUS = {
  draft: '待发布',
  published: '已发布',
  failed: '发布失败',
  offline: '已下线',
}

export const RENDER_STATUS = {
  pending: '待合成',
  rendering: '合成中',
  failed: '合成失败',
  success: '合成成功',
}

export const VISUAL_TYPES = {
  screen_recording: '屏幕录制',
  talking_head: '真人出镜',
  motion_graphics: '动态图形',
  stock_footage: '素材剪辑',
  text_animation: '文字动画',
}

export const COLUMNS = [
  { value: 'auto', label: '系统自动判断' },
  { value: 'one_minute_ai_office', label: '一分钟 AI 办公' },
  { value: 'less_overtime', label: '今天少加班一小时' },
  { value: 'boss_ai', label: '老板也能听懂的 AI' },
  { value: 'ordinary_ai_toolbox', label: '普通人 AI 工具箱' },
  { value: 'ai_pitfall_guide', label: 'AI 避坑指南' },
]

// Tag type mapping for Element Plus el-tag
export const STATUS_TAG_TYPE = {
  pending: 'info',
  running: 'warning',
  success: 'success',
  failed: 'danger',
  cancelled: 'info',
  retrying: 'warning',
  generating: 'warning',
  pending_review: 'info',
  approved: 'success',
  approved_with_edit: 'success',
  rejected: 'danger',
  regenerating: 'warning',
  pending_render: 'info',
  rendering: 'warning',
  render_failed: 'danger',
  rendered: 'success',
  exported: 'success',
  published: 'success',
  offline: 'info',
  draft: 'info',
  enabled: 'success',
  paused: 'warning',
  deleted: 'info',
  usable: 'success',
  not_suitable: 'danger',
  uncertain: 'warning',
}
