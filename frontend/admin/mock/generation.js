let idCounter = 0
function nextId(prefix) {
  return `${prefix}_${String(++idCounter).padStart(3, '0')}`
}

function now() {
  return '2026-05-20 ' + ['09', '10', '11', '12'][Math.floor(Math.random() * 4)] + ':' + String(Math.floor(Math.random() * 60)).padStart(2, '0') + ':' + String(Math.floor(Math.random() * 60)).padStart(2, '0')
}

const taskMap = {}

export default {
  'POST:/generation/create_task': (data) => {
    const taskId = nextId('task')
    const task = {
      id: taskId,
      direction: data.direction,
      topic: data.topic || '',
      audience: data.audience || '',
      count: data.count || 5,
      column: data.column || 'auto',
      generation_type: data.generation_type || 'full_script_storyboard',
      status: 'pending',
      current_stage: 'create_task',
      progress: 0,
      created_at: now(),
      updated_at: now(),
      error_message: '',
    }
    taskMap[taskId] = task
    // Simulate task starting soon
    setTimeout(() => {
      if (taskMap[taskId] && taskMap[taskId].status === 'pending') {
        taskMap[taskId].status = 'running'
      }
    }, 500)
    return {
      code: 0, message: 'success',
      data: { task_id: taskId, status: 'pending', stream_url: `/api/v1/generation/stream/${taskId}` },
    }
  },

  'GET:/generation/get_task_list': (params) => {
    const items = Object.values(taskMap)
    return {
      code: 0, message: 'success',
      data: { items, total: items.length, page: params?.page || 1, page_size: params?.page_size || 20 },
    }
  },

  'GET:/generation/get_task_detail/{id}': (params, id) => {
    const task = taskMap[id]
    if (!task) return { code: 40400, message: '任务不存在', data: null }
    return {
      code: 0, message: 'success',
      data: {
        ...task,
        source_count: 20,
        topic_count: 5,
        script_count: 1,
        logs: [
          { stage: 'fetch_sources', message: '已抓取 20 条相关素材', level: 'info', created_at: now() },
          { stage: 'generate_topics', message: '已生成 5 个选题', level: 'info', created_at: now() },
        ],
      },
    }
  },

  'POST:/generation/cancel_task': (data) => {
    const task = taskMap[data.task_id]
    if (task) { task.status = 'cancelled'; task.updated_at = now() }
    return { code: 0, message: 'success', data: { task_id: data.task_id, status: 'cancelled' } }
  },

  'POST:/generation/retry_task': (data) => {
    const task = taskMap[data.task_id]
    if (task) { task.status = 'retrying'; task.updated_at = now() }
    return { code: 0, message: 'success', data: { task_id: data.task_id, status: 'retrying', stream_url: `/api/v1/generation/stream/${data.task_id}` } }
  },
}
