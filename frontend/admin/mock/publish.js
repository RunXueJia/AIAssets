const records = [
  { id: 'pub_001', package_id: 'pkg_001', title: '用 AI 10 分钟写完一份周报', platform: 'douyin', platform_url: 'https://www.douyin.com/video/xxx', published_at: '2026-05-20 12:00:00', status: 'published', remark: '运营手动发布', created_by_name: '视频运营', created_at: '2026-05-20 12:10:00' },
]

export default {
  'POST:/publish/create_record': (data) => ({
    code: 0, message: 'success', data: { record_id: 'pub_002', status: data.status || 'published' },
  }),

  'POST:/publish/update_record': (data) => ({
    code: 0, message: 'success', data: { record_id: data.record_id, status: data.status },
  }),

  'GET:/publish/get_record_list': (params) => ({
    code: 0, message: 'success',
    data: { items: records, total: records.length, page: params?.page || 1, page_size: params?.page_size || 20 },
  }),
}
