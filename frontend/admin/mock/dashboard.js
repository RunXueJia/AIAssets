export default {
  'GET:/dashboard/get_overview': () => ({
    code: 0, message: 'success',
    data: {
      generation_task_count: 12,
      fetch_task_count: 10,
      source_item_count: 86,
      topic_count: 30,
      script_count: 8,
      video_count: 3,
      pending_review_count: 6,
      render_failed_count: 1,
      package_count: 2,
    },
  }),

  'GET:/dashboard/get_trend': () => ({
    code: 0, message: 'success',
    data: {
      dates: ['2026-05-14', '2026-05-15', '2026-05-16', '2026-05-17', '2026-05-18', '2026-05-19', '2026-05-20'],
      generation_task_counts: [8, 10, 9, 11, 13, 10, 12],
      source_item_counts: [45, 60, 55, 70, 80, 75, 86],
      script_counts: [3, 5, 4, 6, 7, 6, 8],
      video_counts: [1, 1, 2, 2, 3, 2, 3],
      task_success_rate: 0.92,
      task_failed_rate: 0.08,
      fetch_success_rate: 0.9,
      llm_success_rate: 0.95,
      sse_disconnect_rate: 0.03,
      avg_generation_seconds: 180,
      avg_render_seconds: 420,
      package_export_count: 9,
    },
  }),
}
