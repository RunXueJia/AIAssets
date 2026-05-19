export const permissionGroups = [
  {
    title: '系统',
    permissions: ['system:user:read', 'system:role:read', 'system:task:read']
  },
  {
    title: 'LLM',
    permissions: [
      'llm:provider:read',
      'llm:provider:create',
      'llm:provider:update',
      'llm:model:read',
      'llm:model:create',
      'llm:model:update',
      'llm:prompt:read',
      'llm:prompt:create',
      'llm:prompt:update',
      'llm:log:read'
    ]
  },
  {
    title: '内容',
    permissions: [
      'content:channel:read',
      'content:column:read',
      'content:topic:read',
      'content:script:read',
      'content:storyboard:read'
    ]
  },
  {
    title: '审核发布',
    permissions: ['review:content:read', 'asset:video:read', 'publish:queue:read']
  },
  {
    title: '增长数据',
    permissions: ['lead:lead:read', 'dashboard:overview:read', 'report:daily:read']
  }
]

export const adminAllPermissions = permissionGroups.flatMap((group) => group.permissions).concat([
  'llm:prompt:test',
  'content:topic:generate',
  'content:script:generate',
  'content:storyboard:generate',
  'review:content:approve',
  'review:content:reject',
  'publish:queue:update'
])

export function hasPermission(userPermissions = [], required) {
  if (!required || required.length === 0) {
    return true
  }
  const requiredList = Array.isArray(required) ? required : [required]
  return requiredList.every((permission) => userPermissions.includes(permission))
}
