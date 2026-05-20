const packages = [
  { id: 'pkg_001', title: '用 AI 10 分钟写完一份周报', video_id: 'video_001', script_id: 'script_001', platforms: ['douyin', 'xiaohongshu'], file_size: 104857600, download_url: '/api/v1/package/download_package/pkg_001', created_at: '2026-05-20 11:00:00' },
]

export default {
  'POST:/package/create_package': (data) => ({
    code: 0, message: 'success',
    data: { package_id: 'pkg_002', status: 'exported', download_url: '/api/v1/package/download_package/pkg_002' },
  }),

  'GET:/package/get_package_list': (params) => ({
    code: 0, message: 'success',
    data: { items: packages, total: packages.length, page: params?.page || 1, page_size: params?.page_size || 20 },
  }),

  'GET:/package/get_package_detail/{id}': (params, id) => ({
    code: 0, message: 'success',
    data: {
      id, title: '用 AI 10 分钟写完一份周报',
      video_file: { name: 'video.mp4', download_url: '/api/v1/file/download_video/video_001' },
      cover_file: { name: 'cover.jpg', download_url: '/api/v1/file/download_cover/cover_001' },
      platform_title: '用 AI 10 分钟写完周报',
      description: '一个适合普通职场人的 AI 周报写作方法。',
      tags: ['AI办公', '职场效率', '周报'],
      pinned_comment: '试试先整理工作记录，再让 AI 生成周报结构。',
      script_text: '完整口播稿文本...',
      storyboards: [],
      knowledge_cards: [],
      download_draft: '资料包草稿内容',
      download_url: `/api/v1/package/download_package/${id}`,
      created_at: '2026-05-20 11:00:00',
    },
  }),
}
