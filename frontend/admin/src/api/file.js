const BASE = import.meta.env.VITE_API_BASE || '/api/v1'

export function previewVideoUrl(id) {
  return `${BASE}/file/preview_video/${id}`
}

export function downloadVideoUrl(id) {
  return `${BASE}/file/download_video/${id}`
}

export function previewCoverUrl(id) {
  return `${BASE}/file/preview_cover/${id}`
}

export function downloadCoverUrl(id) {
  return `${BASE}/file/download_cover/${id}`
}

export function downloadAssetUrl(id) {
  return `${BASE}/file/download_asset/${id}`
}
