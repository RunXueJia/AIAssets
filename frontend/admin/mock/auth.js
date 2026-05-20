export default {
  'POST:/auth/login': (data) => {
    const { username, password } = data
    if (username === 'admin' && password === 'Admin123456') {
      return {
        code: 0,
        message: 'success',
        data: {
          access_token: 'mock-jwt-token-admin',
          token_type: 'Bearer',
          expires_in: 7200,
          user: {
            id: 'u_001',
            username: 'admin',
            display_name: '管理员',
            role: 'admin',
            permissions: ['*'],
            created_at: '2026-05-20 09:00:00',
          },
        },
      }
    }
    if (username === 'editor01' && password === '123456') {
      return {
        code: 0,
        message: 'success',
        data: {
          access_token: 'mock-jwt-token-editor',
          token_type: 'Bearer',
          expires_in: 7200,
          user: {
            id: 'u_002',
            username: 'editor01',
            display_name: '内容编辑01',
            role: 'content_editor',
            permissions: ['generation:view', 'source:view', 'topic:manage', 'script:manage', 'review:manage'],
            created_at: '2026-05-20 09:00:00',
          },
        },
      }
    }
    if (username === 'video01' && password === '123456') {
      return {
        code: 0,
        message: 'success',
        data: {
          access_token: 'mock-jwt-token-video',
          token_type: 'Bearer',
          expires_in: 7200,
          user: {
            id: 'u_003',
            username: 'video01',
            display_name: '视频运营',
            role: 'video_operator',
            permissions: ['render:manage', 'package:manage', 'publish:manage', 'file:download'],
            created_at: '2026-05-20 09:00:00',
          },
        },
      }
    }
    if (username === 'viewer01' && password === '123456') {
      return {
        code: 0,
        message: 'success',
        data: {
          access_token: 'mock-jwt-token-viewer',
          token_type: 'Bearer',
          expires_in: 7200,
          user: {
            id: 'u_004',
            username: 'viewer01',
            display_name: '只读查看者',
            role: 'viewer',
            permissions: ['dashboard:view', 'generation:view', 'source:view', 'topic:view', 'script:view', 'report:view'],
            created_at: '2026-05-20 09:00:00',
          },
        },
      }
    }
    return { code: 40001, message: '用户名或密码错误', data: null }
  },

  'POST:/auth/logout': () => ({
    code: 0, message: 'success', data: true,
  }),

  'GET:/auth/me': () => ({
    code: 0,
    message: 'success',
    data: {
      id: 'u_001',
      username: 'admin',
      display_name: '管理员',
      role: 'admin',
      permissions: ['*'],
      created_at: '2026-05-20 09:00:00',
    },
  }),
}
