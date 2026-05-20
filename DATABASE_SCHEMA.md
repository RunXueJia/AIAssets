# 24小时AI增长资产引擎数据库表结构设计

版本：v1.0  
日期：2026-05-20  
数据库：MySQL 8  
字符集：utf8mb4

## 1. 设计原则

- 统一使用 `VARCHAR(32)` 作为业务主键，便于前后端传递和人工排查。
- 统一使用 `created_at`、`updated_at`，可编辑表补充 `deleted_at`。
- 枚举值使用稳定字符串，不直接依赖中文显示文案。
- 长文本使用 `LONGTEXT`，结构化扩展字段使用 `JSON`。
- 任务类、内容类、日志类分表存储，避免单表过大。
- 审核、版本和日志不做物理删除，保留追溯链路。

## 2. 状态字典

### 2.1 通用状态

- `pending`：等待中
- `running`：运行中
- `success`：成功
- `failed`：失败
- `cancelled`：已取消
- `retrying`：重试中

### 2.2 内容状态

- `generating`：生成中
- `pending_review`：待审核
- `approved`：审核通过
- `approved_with_edit`：修改后通过
- `rejected`：驳回
- `regenerating`：重新生成中
- `pending_render`：待合成
- `rendering`：合成中
- `render_failed`：合成失败
- `rendered`：已合成
- `exported`：已导出
- `published`：已发布
- `offline`：已下线

### 2.3 来源状态

- `usable`：可用
- `not_suitable`：不适合使用
- `uncertain`：需要人工确认

### 2.4 监控状态

- `enabled`：运行中
- `paused`：已暂停
- `deleted`：已删除

### 2.5 生成类型

- `topics_only`
- `topics_and_script`
- `full_script_storyboard`

## 3. 表关系总览

- `role` 1 - N `user`
- `role` N - N `permission`，通过 `role_permission`
- `generation_task` 1 - N `source_summary`
- `source_summary` 1 - N `source_item`
- `generation_task` 1 - N `topic`
- `topic` 1 - N `script`
- `script` 1 - N `storyboard`
- `script` 1 - N `subtitle`
- `script` 1 - N `review_record`
- `script` 1 - 1 `render_task`
- `render_task` 1 - 1 `video_asset`
- `script` 1 - 1 `cover_asset`
- `script` 1 - 1 `card_asset`
- `script` 1 - 1 `download_asset`
- `script` 1 - 1 `publish_package`
- `publish_package` 1 - N `publish_record`
- `task_log` 记录所有任务事件
- `audit_log` 记录后台操作审计
- `daily_report` 按日期汇总
- `system_setting` 按键值存储

## 4. 表结构

### 4.1 role

后台角色表。

- `id` 主键
- `code` 角色编码，唯一
- `name` 角色名称
- `description` 说明
- `status` 启用状态
- `sort_order` 排序
- `created_at` / `updated_at`

索引：

- `uk_role_code`

### 4.2 permission

权限表，覆盖菜单、按钮和 API 权限。

- `id`
- `code` 权限编码，唯一
- `name` 权限名称
- `type` 权限类型，`menu` / `button` / `api`
- `module` 模块名
- `action` 动作名
- `description`
- `status`
- `sort_order`
- `created_at` / `updated_at`

索引：

- `uk_permission_code`
- `idx_permission_module_type`

### 4.3 role_permission

角色权限关联表。

- `id`
- `role_id`
- `permission_id`
- `created_at`

索引：

- `uk_role_permission_role_permission`
- `idx_role_permission_permission_id`

### 4.4 user

后台用户表。

- `id`
- `username` 登录名，唯一
- `password_hash`
- `display_name`
- `avatar_url`
- `phone`
- `email`
- `role_id`
- `status`
- `last_login_at`
- `last_login_ip`
- `deleted_at`
- `created_at` / `updated_at`

索引：

- `uk_user_username`
- `idx_user_role_id`
- `idx_user_status`

### 4.5 audit_log

后台操作审计表。

- `id`
- `user_id`
- `username`
- `module`
- `action`
- `resource_type`
- `resource_id`
- `request_method`
- `request_path`
- `request_params_json`
- `response_status`
- `ip`
- `user_agent`
- `result`
- `message`
- `created_at`

索引：

- `idx_audit_log_user_id_created_at`
- `idx_audit_log_resource`
- `idx_audit_log_created_at`

### 4.6 generation_task

生成任务主表，承接内容生成入口。

- `id`
- `direction`
- `topic`
- `audience`
- `count`
- `column_code`
- `generation_type`
- `start_mode`
- `status`
- `current_stage`
- `progress`
- `retry_count`
- `parent_task_id`
- `source_summary_id`
- `selected_topic_id`
- `final_script_id`
- `final_render_task_id`
- `input_payload_json`
- `result_payload_json`
- `error_message`
- `error_code`
- `started_at`
- `finished_at`
- `created_by`
- `updated_by`
- `deleted_at`
- `created_at` / `updated_at`

索引：

- `idx_generation_task_status_created_at`
- `idx_generation_task_created_by`
- `idx_generation_task_current_stage`
- `idx_generation_task_source_summary_id`

### 4.7 render_task

视频合成任务表。

- `id`
- `generation_task_id`
- `script_id`
- `template_code`
- `status`
- `progress`
- `retry_count`
- `start_mode`
- `input_payload_json`
- `output_video_asset_id`
- `error_message`
- `started_at`
- `finished_at`
- `created_by`
- `updated_by`
- `created_at` / `updated_at`

索引：

- `idx_render_task_script_id`
- `idx_render_task_status_created_at`
- `idx_render_task_generation_task_id`

### 4.8 monitor_task

话题监控任务表。

- `id`
- `topic`
- `audience`
- `schedule_time`
- `fetch_limit`
- `auto_generate_topics`
- `status`
- `cron_expression`
- `last_run_at`
- `next_run_at`
- `last_summary_id`
- `created_by`
- `updated_by`
- `deleted_at`
- `created_at` / `updated_at`

索引：

- `idx_monitor_task_status`
- `idx_monitor_task_next_run_at`
- `idx_monitor_task_created_by`

### 4.9 source_summary

素材汇总表，区分生成任务汇总和每日监控汇总。

- `id`
- `summary_type`，`generation` / `monitor_daily`
- `generation_task_id`
- `monitor_task_id`
- `summary_date`
- `title`
- `summary_text`
- `key_points_json`
- `risk_notes_json`
- `source_count`
- `usable_source_count`
- `need_human_confirm`
- `llm_model_name`
- `llm_raw_output`
- `created_by`
- `created_at` / `updated_at`

索引：

- `idx_source_summary_generation_task_id`
- `idx_source_summary_monitor_task_id_summary_date`
- `idx_source_summary_type_created_at`

### 4.10 source_item

抓取来源表。

- `id`
- `source_summary_id`
- `generation_task_id`
- `monitor_task_id`
- `source_hash`
- `title`
- `site_name`
- `url`
- `author`
- `published_at`
- `summary_text`
- `relevance_reason`
- `key_points_json`
- `raw_content_text`
- `status`
- `need_human_confirm`
- `fetch_status`
- `fetch_error_message`
- `source_order`
- `created_at` / `updated_at`

索引：

- `idx_source_item_source_summary_id`
- `idx_source_item_generation_task_id`
- `idx_source_item_monitor_task_id`
- `idx_source_item_status`
- `idx_source_item_source_hash`
- `idx_source_item_url`

### 4.11 topic

候选选题表。

- `id`
- `generation_task_id`
- `source_summary_id`
- `title`
- `audience`
- `angle`
- `recommended_column`
- `duration_seconds`
- `keywords_json`
- `reason`
- `score`
- `status`
- `need_human_confirm`
- `lock_user_id`
- `lock_at`
- `reject_reason`
- `approved_by`
- `approved_at`
- `created_at` / `updated_at`

索引：

- `idx_topic_generation_task_id`
- `idx_topic_source_summary_id`
- `idx_topic_status`
- `idx_topic_lock_user_id`

### 4.12 script

脚本主表，保存当前版本内容。

- `id`
- `topic_id`
- `generation_task_id`
- `source_summary_id`
- `title`
- `hook`
- `pain_point`
- `method`
- `steps_json`
- `example_text`
- `summary_text`
- `cta_text`
- `platform_title`
- `description`
- `tags_json`
- `cover_text`
- `pinned_comment`
- `status`
- `current_version_no`
- `need_human_confirm`
- `risk_notes_json`
- `created_at` / `updated_at`

索引：

- `idx_script_topic_id`
- `idx_script_generation_task_id`
- `idx_script_status`

### 4.13 storyboard

分镜明细表。

- `id`
- `script_id`
- `shot_no`
- `duration_seconds`
- `voiceover`
- `subtitle`
- `visual_type`
- `material_suggestion`
- `motion_suggestion`
- `scene_note`
- `status`
- `created_at` / `updated_at`

索引：

- `uk_storyboard_script_shot_no`
- `idx_storyboard_script_id`

### 4.14 subtitle

字幕明细表。

- `id`
- `script_id`
- `line_no`
- `start_time_ms`
- `end_time_ms`
- `text`
- `speaker`
- `style_name`
- `status`
- `created_at` / `updated_at`

索引：

- `uk_subtitle_script_line_no`
- `idx_subtitle_script_id`

### 4.15 content_version

内容版本表，用于脚本、分镜和字幕留痕。

- `id`
- `content_type`，`script` / `storyboard` / `subtitle`
- `content_id`
- `version_no`
- `payload_json`
- `change_note`
- `operator_id`
- `created_at`

索引：

- `uk_content_version_type_id_no`
- `idx_content_version_content_id`

### 4.16 review_record

审核记录表。

- `id`
- `content_type`
- `content_id`
- `generation_task_id`
- `action`
- `before_status`
- `after_status`
- `reason`
- `comment`
- `edited_payload_json`
- `reviewer_id`
- `reviewer_name`
- `created_at`

索引：

- `idx_review_record_content`
- `idx_review_record_generation_task_id`
- `idx_review_record_reviewer_id`

### 4.17 video_asset

视频资产表。

- `id`
- `script_id`
- `render_task_id`
- `file_name`
- `file_path`
- `storage_provider`
- `file_size`
- `mime_type`
- `width`
- `height`
- `duration_seconds`
- `checksum`
- `status`
- `created_at` / `updated_at`

索引：

- `idx_video_asset_script_id`
- `idx_video_asset_render_task_id`

### 4.18 cover_asset

封面资产表。

- `id`
- `script_id`
- `package_id`
- `file_name`
- `file_path`
- `storage_provider`
- `file_size`
- `mime_type`
- `width`
- `height`
- `checksum`
- `status`
- `created_at` / `updated_at`

索引：

- `idx_cover_asset_script_id`
- `idx_cover_asset_package_id`

### 4.19 card_asset

知识卡片资产表。

- `id`
- `script_id`
- `package_id`
- `file_name`
- `file_path`
- `storage_provider`
- `file_size`
- `mime_type`
- `checksum`
- `status`
- `created_at` / `updated_at`

索引：

- `idx_card_asset_script_id`
- `idx_card_asset_package_id`

### 4.20 download_asset

资料包草稿表。

- `id`
- `script_id`
- `package_id`
- `draft_name`
- `draft_text`
- `file_name`
- `file_path`
- `storage_provider`
- `file_size`
- `mime_type`
- `checksum`
- `status`
- `created_at` / `updated_at`

索引：

- `idx_download_asset_script_id`
- `idx_download_asset_package_id`

### 4.21 publish_package

发布包主表。

- `id`
- `script_id`
- `render_task_id`
- `video_asset_id`
- `cover_asset_id`
- `card_asset_id`
- `download_asset_id`
- `package_name`
- `platform_title`
- `description`
- `tags_json`
- `pinned_comment`
- `platforms_json`
- `package_status`
- `file_name`
- `file_path`
- `file_size`
- `checksum`
- `exported_by`
- `exported_at`
- `created_at` / `updated_at`

索引：

- `idx_publish_package_script_id`
- `idx_publish_package_render_task_id`
- `idx_publish_package_status`

### 4.22 publish_record

发布记录回填表。

- `id`
- `package_id`
- `script_id`
- `platform`
- `platform_url`
- `published_at`
- `status`
- `remark`
- `created_by`
- `updated_by`
- `created_at` / `updated_at`

索引：

- `idx_publish_record_package_id`
- `idx_publish_record_platform`
- `idx_publish_record_status`

### 4.23 task_log

任务日志表，覆盖生成、监控、合成、日报等异步过程。

- `id`
- `task_type`
- `task_id`
- `generation_task_id`
- `monitor_task_id`
- `related_content_type`
- `related_content_id`
- `event_type`
- `stage`
- `level`
- `message`
- `detail_json`
- `error_code`
- `error_message`
- `created_at`

索引：

- `idx_task_log_task_type_task_id`
- `idx_task_log_related_content`
- `idx_task_log_level_created_at`
- `idx_task_log_created_at`

### 4.24 daily_report

每日报告表。

- `id`
- `report_date`
- `title`
- `generation_task_count`
- `source_item_count`
- `topic_count`
- `script_count`
- `storyboard_count`
- `subtitle_count`
- `render_count`
- `package_count`
- `failed_task_count`
- `success_rate`
- `overview_json`
- `content_json`
- `markdown_path`
- `pdf_path`
- `created_at` / `updated_at`

索引：

- `uk_daily_report_report_date`

### 4.25 system_setting

系统设置表，按键值存储。

- `id`
- `setting_key`
- `setting_name`
- `setting_group`
- `setting_value_json`
- `value_type`
- `is_secret`
- `scope`
- `description`
- `updated_by`
- `created_at` / `updated_at`

索引：

- `uk_system_setting_key`
- `idx_system_setting_group`

## 5. 建议约束

- `role.code`、`permission.code`、`system_setting.setting_key` 使用唯一约束。
- `storyboard` 以 `script_id + shot_no` 唯一。
- `subtitle` 以 `script_id + line_no` 唯一。
- `content_version` 以 `content_type + content_id + version_no` 唯一。
- `daily_report.report_date` 唯一。
- `source_item.source_hash` 用于去重，建议建普通索引或按业务规则设唯一约束。
- 所有业务写表都要记录 `created_at` 和 `updated_at`。

## 6. 落库优先级

P0 先建：

- `role`
- `permission`
- `role_permission`
- `user`
- `generation_task`
- `monitor_task`
- `source_summary`
- `source_item`
- `topic`
- `script`
- `storyboard`
- `subtitle`
- `review_record`
- `render_task`
- `video_asset`
- `publish_package`
- `publish_record`
- `task_log`
- `system_setting`

P1 再建：

- `audit_log`
- `content_version`
- `cover_asset`
- `card_asset`
- `download_asset`
- `daily_report`

## 7. 说明

这份设计偏向 MVP 可落地，不把所有扩展能力提前做成复杂配置表。后续如果要细化栏目、模板、来源站点规则或多租户权限，可以在这套结构上再加维表，不需要推倒重来。
