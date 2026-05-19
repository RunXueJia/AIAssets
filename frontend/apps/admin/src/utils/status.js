export const statusMaps = {
  enabled: { label: '启用', type: 'success' },
  disabled: { label: '停用', type: 'info' },
  generated: { label: '已生成', type: 'success' },
  locked: { label: '已锁定', type: 'warning' },
  draft: { label: '草稿', type: 'info' },
  pending_review: { label: '待审核', type: 'warning' },
  approved: { label: '已通过', type: 'success' },
  rejected: { label: '已驳回', type: 'danger' },
  regenerating: { label: '重新生成', type: 'warning' },
  waiting: { label: '等待中', type: 'info' },
  rendering: { label: '合成中', type: 'warning' },
  success: { label: '成功', type: 'success' },
  failed: { label: '失败', type: 'danger' },
  pending_publish: { label: '待发布', type: 'warning' },
  published: { label: '已发布', type: 'success' },
  offline: { label: '已下线', type: 'info' },
  queued: { label: '排队中', type: 'info' },
  running: { label: '运行中', type: 'warning' },
  streaming: { label: '流式输出', type: 'warning' },
  repaired: { label: '已修复', type: 'success' },
  interrupted: { label: '已中断', type: 'danger' },
  cancelled: { label: '已取消', type: 'info' },
  retrying: { label: '重试中', type: 'warning' }
}

export function getStatusMeta(status) {
  return statusMaps[status] || { label: status || '-', type: 'info' }
}
