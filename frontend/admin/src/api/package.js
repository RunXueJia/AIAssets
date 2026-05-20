import request from './request'

export function createPackage(scriptId, videoId, platforms) {
  return request.post('/package/create_package', { script_id: scriptId, video_id: videoId, platforms }).then((r) => r.data)
}

export function getPackageList(params) {
  return request.get('/package/get_package_list', params).then((r) => r.data)
}

export function getPackageDetail(id) {
  return request.get(`/package/get_package_detail/${id}`).then((r) => r.data)
}

export function getPackageDownloadUrl(id) {
  const base = import.meta.env.VITE_API_BASE || '/api/v1'
  return `${base}/package/download_package/${id}`
}
