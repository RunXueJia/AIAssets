import { useAuthStore } from '@/stores/auth'

export function hasPermission(permission) {
  const auth = useAuthStore()
  if (!auth.permissions || auth.permissions.length === 0) return false
  if (auth.permissions.includes('*')) return true
  return auth.permissions.includes(permission)
}

export function hasAnyPermission(permissions) {
  return permissions.some((p) => hasPermission(p))
}

export function getRoleLabel(role) {
  const { ROLES } = require('@/utils/constants')
  return ROLES[role] || role
}
