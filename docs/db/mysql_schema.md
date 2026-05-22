# MySQL 表结构设计

## 1. 设计原则

- 数据库：MySQL 8.0+，字符集 `utf8mb4`，排序规则 `utf8mb4_0900_ai_ci`。
- 主键：所有业务表统一使用 `BIGINT UNSIGNED AUTO_INCREMENT`。
- 关联：不使用数据库外键，通过 `*_id` 字段做逻辑关联，由 Service 层保证一致性。
- 时间：所有表保留 `created_at`、`updated_at`，需要软删除的业务表增加 `deleted_at`。
- 枚举：使用 `VARCHAR` 存储业务状态，枚举值在后端常量或 Pydantic Schema 中约束。
- 快照：用户输入、AI 输出、地图、天气、实时信息等易变化数据都保存快照，保证历史记录可复现。
- 敏感信息：API Key 只保存密文和掩码，不在普通日志、前端响应、调用日志中保存明文。

## 2. 核心关系

```text
users
  ├── login_sessions
  ├── generation_records
  │     ├── generation_inputs
  │     ├── generation_outputs
  │     ├── generation_stream_events
  │     ├── generation_errors
  │     ├── route_snapshots
  │     ├── route_map_exports
  │     ├── weather_snapshots
  │     ├── news_snapshots
  │     └── llm_call_logs
  ├── llm_configs         管理员创建/更新
  └── config_audit_logs   管理员配置审计
```

## 3. 账号与会话

### 3.1 users

统一保存游客、普通用户和管理员账号。管理员通过 `role = 'admin'` 区分，不单独拆 `admin_users`。

```sql
CREATE TABLE users (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '用户ID',
  username VARCHAR(64) NULL COMMENT '用户名',
  nickname VARCHAR(64) NULL COMMENT '显示名称',
  email VARCHAR(128) NULL COMMENT '邮箱',
  phone VARCHAR(32) NULL COMMENT '手机号',
  password_hash VARCHAR(255) NULL COMMENT '密码哈希，游客可为空',
  role VARCHAR(20) NOT NULL DEFAULT 'user' COMMENT 'guest/user/admin',
  status VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT 'active/disabled',
  guest_token_hash VARCHAR(128) NULL COMMENT '游客会话标识哈希',
  last_login_at DATETIME NULL COMMENT '最近登录时间',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  deleted_at DATETIME NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uk_users_username (username),
  UNIQUE KEY uk_users_email (email),
  UNIQUE KEY uk_users_phone (phone),
  KEY idx_users_role_status (role, status),
  KEY idx_users_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='用户账号';
```

### 3.2 login_sessions

保存登录态、游客临时会话、刷新令牌和失效控制。

```sql
CREATE TABLE login_sessions (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '会话ID',
  user_id BIGINT UNSIGNED NOT NULL COMMENT '用户ID',
  session_token_hash VARCHAR(128) NOT NULL COMMENT '会话令牌哈希',
  refresh_token_hash VARCHAR(128) NULL COMMENT '刷新令牌哈希',
  client_type VARCHAR(20) NOT NULL DEFAULT 'web' COMMENT 'web/admin',
  ip_address VARCHAR(64) NULL COMMENT '登录IP',
  user_agent VARCHAR(500) NULL COMMENT 'User-Agent',
  expires_at DATETIME NOT NULL COMMENT '过期时间',
  revoked_at DATETIME NULL COMMENT '注销/失效时间',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_login_sessions_token (session_token_hash),
  KEY idx_login_sessions_user_id (user_id),
  KEY idx_login_sessions_expires_at (expires_at),
  KEY idx_login_sessions_revoked_at (revoked_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='登录会话';
```

## 4. 生成记录

### 4.1 generation_records

用户端历史记录和管理端生成记录列表的主表。列表页优先查这张表，不扫描大 JSON。

```sql
CREATE TABLE generation_records (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '生成记录ID',
  record_no VARCHAR(40) NOT NULL COMMENT '业务编号',
  user_id BIGINT UNSIGNED NOT NULL COMMENT '用户ID',
  source_client VARCHAR(20) NOT NULL DEFAULT 'web' COMMENT 'web/admin/api',
  origin_text VARCHAR(255) NOT NULL COMMENT '起点展示文本',
  destination_text VARCHAR(255) NOT NULL COMMENT '目的地展示文本',
  range_text VARCHAR(120) NOT NULL COMMENT '范围/天数展示文本',
  transport_mode VARCHAR(30) NOT NULL COMMENT 'driving/transit/walking/cycling/motorcycle/mixed',
  status VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT 'pending/streaming/completed/failed/canceled',
  current_stage VARCHAR(40) NULL COMMENT '当前生成阶段',
  summary_title VARCHAR(160) NULL COMMENT '历史列表标题',
  summary_text VARCHAR(500) NULL COMMENT '结果摘要',
  started_at DATETIME NULL COMMENT '开始生成时间',
  completed_at DATETIME NULL COMMENT '完成时间',
  canceled_at DATETIME NULL COMMENT '取消时间',
  failed_at DATETIME NULL COMMENT '失败时间',
  duration_ms INT UNSIGNED NULL COMMENT '总耗时毫秒',
  retry_count INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '重试次数',
  parent_record_id BIGINT UNSIGNED NULL COMMENT '重新生成来源记录ID',
  error_code VARCHAR(80) NULL COMMENT '最近错误码',
  error_message VARCHAR(500) NULL COMMENT '最近错误摘要',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  deleted_at DATETIME NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uk_generation_records_no (record_no),
  KEY idx_generation_records_user_created (user_id, created_at),
  KEY idx_generation_records_status_created (status, created_at),
  KEY idx_generation_records_transport_created (transport_mode, created_at),
  KEY idx_generation_records_parent (parent_record_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='生成记录主表';
```

### 4.2 generation_inputs

保存用户输入快照，避免用户后续修改资料影响历史结果。

```sql
CREATE TABLE generation_inputs (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '输入快照ID',
  record_id BIGINT UNSIGNED NOT NULL COMMENT '生成记录ID',
  origin_text VARCHAR(255) NOT NULL COMMENT '起点原始文本',
  destination_text VARCHAR(255) NOT NULL COMMENT '目的地原始文本',
  range_text VARCHAR(120) NOT NULL COMMENT '范围原始文本',
  transport_mode VARCHAR(30) NOT NULL COMMENT '交通方式',
  travel_date DATE NULL COMMENT '出行日期',
  date_text VARCHAR(120) NULL COMMENT '模糊日期文本',
  people_count INT UNSIGNED NULL COMMENT '人数',
  preferences JSON NULL COMMENT '偏好列表',
  avoidances JSON NULL COMMENT '避免项列表',
  raw_input JSON NOT NULL COMMENT '完整输入快照',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_generation_inputs_record (record_id),
  KEY idx_generation_inputs_transport (transport_mode),
  KEY idx_generation_inputs_travel_date (travel_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='生成输入快照';
```

### 4.3 generation_outputs

保存最终 Markdown、结构化 JSON、地图链接等结果。

```sql
CREATE TABLE generation_outputs (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '输出结果ID',
  record_id BIGINT UNSIGNED NOT NULL COMMENT '生成记录ID',
  final_markdown MEDIUMTEXT NULL COMMENT '最终Markdown',
  result_json JSON NULL COMMENT '结构化结果',
  weather_summary TEXT NULL COMMENT '天气摘要',
  route_summary TEXT NULL COMMENT '路线摘要',
  attractions_summary TEXT NULL COMMENT '途径景点摘要',
  realtime_info_summary TEXT NULL COMMENT '实时信息摘要',
  risk_summary TEXT NULL COMMENT '风险提示摘要',
  amap_route_url TEXT NULL COMMENT '高德路线链接',
  map_export_id BIGINT UNSIGNED NULL COMMENT '默认路径图导出ID',
  output_version INT UNSIGNED NOT NULL DEFAULT 1 COMMENT '输出版本',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_generation_outputs_record (record_id),
  KEY idx_generation_outputs_map_export (map_export_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='生成输出结果';
```

### 4.4 generation_stream_events

按需保存流式输出事件，支持用户端回放、失败恢复和后台排查。

```sql
CREATE TABLE generation_stream_events (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '流式事件ID',
  record_id BIGINT UNSIGNED NOT NULL COMMENT '生成记录ID',
  sequence_no INT UNSIGNED NOT NULL COMMENT '事件序号',
  event_type VARCHAR(30) NOT NULL COMMENT 'stage_start/token/message/tool/error/done',
  stage VARCHAR(40) NULL COMMENT '阶段',
  content MEDIUMTEXT NULL COMMENT '事件内容',
  payload JSON NULL COMMENT '事件载荷',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_stream_events_record_seq (record_id, sequence_no),
  KEY idx_stream_events_record_created (record_id, created_at),
  KEY idx_stream_events_type (event_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='流式输出事件';
```

### 4.5 generation_errors

保存异常详情，管理端查看错误、失败重试时使用。

```sql
CREATE TABLE generation_errors (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '错误ID',
  record_id BIGINT UNSIGNED NOT NULL COMMENT '生成记录ID',
  stage VARCHAR(40) NULL COMMENT '出错阶段',
  error_source VARCHAR(40) NOT NULL COMMENT 'llm/amap/weather/realtime/system',
  error_code VARCHAR(80) NULL COMMENT '错误码',
  error_message VARCHAR(1000) NOT NULL COMMENT '错误信息',
  error_detail JSON NULL COMMENT '错误详情',
  retryable TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否可重试',
  handled_by BIGINT UNSIGNED NULL COMMENT '处理管理员ID',
  handled_at DATETIME NULL COMMENT '处理时间',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_generation_errors_record (record_id),
  KEY idx_generation_errors_record_created (record_id, created_at, id),
  KEY idx_generation_errors_source_created (error_source, created_at),
  KEY idx_generation_errors_retryable (retryable)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='生成错误记录';
```

## 5. 外部数据快照

### 5.1 route_snapshots

保存高德地理编码、POI、路径规划等结果快照。

```sql
CREATE TABLE route_snapshots (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '路线快照ID',
  record_id BIGINT UNSIGNED NOT NULL COMMENT '生成记录ID',
  provider VARCHAR(30) NOT NULL DEFAULT 'amap' COMMENT '地图供应商',
  route_type VARCHAR(30) NOT NULL COMMENT 'geocode/poi/driving/transit/walking/cycling/motorcycle',
  origin_location VARCHAR(64) NULL COMMENT '起点经纬度',
  destination_location VARCHAR(64) NULL COMMENT '终点经纬度',
  waypoints JSON NULL COMMENT '途经点',
  distance_m INT UNSIGNED NULL COMMENT '距离米',
  duration_s INT UNSIGNED NULL COMMENT '耗时秒',
  request_params JSON NOT NULL COMMENT '请求参数快照',
  response_data JSON NOT NULL COMMENT '响应数据快照',
  source_updated_at DATETIME NULL COMMENT '供应商数据时间',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_route_snapshots_record (record_id),
  KEY idx_route_snapshots_record_created (record_id, created_at, id),
  KEY idx_route_snapshots_type_created (route_type, created_at),
  KEY idx_route_snapshots_provider (provider)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='地图路线快照';
```

### 5.2 route_map_exports

保存高德路线链接、静态图或截图资源。

```sql
CREATE TABLE route_map_exports (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '路径图导出ID',
  record_id BIGINT UNSIGNED NOT NULL COMMENT '生成记录ID',
  route_snapshot_id BIGINT UNSIGNED NULL COMMENT '路线快照ID',
  export_type VARCHAR(30) NOT NULL COMMENT 'amap_uri/static_image/screenshot',
  status VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT 'pending/completed/failed',
  amap_route_url TEXT NULL COMMENT '高德路线链接',
  image_url TEXT NULL COMMENT '图片访问地址',
  storage_path VARCHAR(500) NULL COMMENT '本地或对象存储路径',
  width INT UNSIGNED NULL COMMENT '图片宽度',
  height INT UNSIGNED NULL COMMENT '图片高度',
  error_message VARCHAR(500) NULL COMMENT '导出错误',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_route_map_exports_record (record_id),
  KEY idx_route_map_exports_record_created (record_id, created_at, id),
  KEY idx_route_map_exports_snapshot (route_snapshot_id),
  KEY idx_route_map_exports_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='路径图导出';
```

### 5.3 weather_snapshots

保存目的地和沿途天气预警快照。

```sql
CREATE TABLE weather_snapshots (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '天气快照ID',
  record_id BIGINT UNSIGNED NOT NULL COMMENT '生成记录ID',
  provider VARCHAR(30) NOT NULL COMMENT '天气供应商',
  city_name VARCHAR(80) NOT NULL COMMENT '城市',
  location VARCHAR(64) NULL COMMENT '经纬度',
  weather_date DATE NULL COMMENT '天气日期',
  weather_summary VARCHAR(500) NULL COMMENT '天气摘要',
  alert_level VARCHAR(30) NULL COMMENT '预警级别',
  alerts JSON NULL COMMENT '预警列表',
  request_params JSON NOT NULL COMMENT '请求参数快照',
  response_data JSON NOT NULL COMMENT '响应数据快照',
  source_updated_at DATETIME NULL COMMENT '供应商更新时间',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_weather_snapshots_record (record_id),
  KEY idx_weather_snapshots_record_created (record_id, created_at, id),
  KEY idx_weather_snapshots_city_date (city_name, weather_date),
  KEY idx_weather_snapshots_alert (alert_level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='天气快照';
```

### 5.4 news_snapshots

保存实时信息检索结果快照。第一期包含两类：新闻/交通管制、攻略/避坑参考。表名沿用 `news_snapshots`，业务含义扩展为实时信息快照。

```sql
CREATE TABLE news_snapshots (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '实时信息快照ID',
  record_id BIGINT UNSIGNED NOT NULL COMMENT '生成记录ID',
  provider VARCHAR(30) NOT NULL COMMENT '搜索供应商',
  query_text VARCHAR(255) NOT NULL COMMENT '查询关键词',
  category VARCHAR(30) NOT NULL DEFAULT 'news' COMMENT 'news/traffic/guide/pitfall',
  item_count INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '结果数量',
  top_titles JSON NULL COMMENT '标题摘要',
  source_sites JSON NULL COMMENT '来源站点摘要',
  credibility_score DECIMAL(5,2) NULL COMMENT '综合可信度评分',
  response_data JSON NOT NULL COMMENT '响应数据快照',
  source_updated_at DATETIME NULL COMMENT '供应商更新时间',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_news_snapshots_record (record_id),
  KEY idx_news_snapshots_record_created (record_id, created_at, id),
  KEY idx_news_snapshots_query_created (query_text, created_at),
  KEY idx_news_snapshots_category (category),
  KEY idx_news_snapshots_provider_category (provider, category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='实时信息检索快照';
```

### 5.5 external_api_cache

通用外部接口缓存，优先缓存高德、天气、实时信息检索低频变化结果。

```sql
CREATE TABLE external_api_cache (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '缓存ID',
  provider VARCHAR(30) NOT NULL COMMENT '供应商',
  api_name VARCHAR(80) NOT NULL COMMENT '接口名称',
  cache_key CHAR(64) NOT NULL COMMENT '请求摘要SHA256',
  request_params JSON NOT NULL COMMENT '请求参数',
  response_data JSON NOT NULL COMMENT '响应数据',
  expires_at DATETIME NOT NULL COMMENT '过期时间',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_external_api_cache_key (provider, api_name, cache_key),
  KEY idx_external_api_cache_expires (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='外部接口缓存';
```

## 6. LLM 配置与调用

### 6.1 llm_configs

管理端配置 LLM 供应商、Base URL、模型名、API Key。

```sql
CREATE TABLE llm_configs (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'LLM配置ID',
  name VARCHAR(80) NOT NULL COMMENT '配置名称',
  provider VARCHAR(50) NOT NULL COMMENT '供应商',
  api_format VARCHAR(50) NOT NULL DEFAULT 'openai_chat_completions' COMMENT 'API格式',
  base_url VARCHAR(500) NOT NULL COMMENT 'Base URL',
  model_name VARCHAR(120) NOT NULL COMMENT '模型名',
  api_key_encrypted TEXT NOT NULL COMMENT 'API Key密文',
  api_key_masked VARCHAR(80) NOT NULL COMMENT 'API Key掩码',
  status VARCHAR(20) NOT NULL DEFAULT 'disabled' COMMENT 'enabled/disabled',
  is_default TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否默认配置',
  timeout_s INT UNSIGNED NOT NULL DEFAULT 60 COMMENT '超时时间秒',
  max_tokens INT UNSIGNED NULL COMMENT '最大输出Token',
  temperature DECIMAL(4,3) NULL COMMENT '温度',
  last_test_status VARCHAR(20) NULL COMMENT 'success/failed',
  last_test_message VARCHAR(500) NULL COMMENT '最近测试信息',
  last_test_at DATETIME NULL COMMENT '最近测试时间',
  created_by BIGINT UNSIGNED NOT NULL COMMENT '创建管理员ID',
  updated_by BIGINT UNSIGNED NULL COMMENT '更新管理员ID',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  deleted_at DATETIME NULL,
  PRIMARY KEY (id),
  KEY idx_llm_configs_status_default (status, is_default),
  KEY idx_llm_configs_provider_model (provider, model_name),
  KEY idx_llm_configs_created_by (created_by)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='LLM配置';
```

### 6.2 llm_call_logs

记录 LLM 调用耗时、Token 消耗和错误，用于后台详情和成本统计。

```sql
CREATE TABLE llm_call_logs (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'LLM调用日志ID',
  record_id BIGINT UNSIGNED NULL COMMENT '生成记录ID',
  llm_config_id BIGINT UNSIGNED NULL COMMENT 'LLM配置ID',
  provider VARCHAR(50) NOT NULL COMMENT '供应商',
  model_name VARCHAR(120) NOT NULL COMMENT '模型名',
  call_type VARCHAR(30) NOT NULL COMMENT 'stream/test/retry',
  status VARCHAR(20) NOT NULL COMMENT 'success/failed/canceled',
  prompt_tokens INT UNSIGNED NULL COMMENT '输入Token',
  completion_tokens INT UNSIGNED NULL COMMENT '输出Token',
  total_tokens INT UNSIGNED NULL COMMENT '总Token',
  duration_ms INT UNSIGNED NULL COMMENT '耗时毫秒',
  request_id VARCHAR(120) NULL COMMENT '供应商请求ID',
  error_code VARCHAR(80) NULL COMMENT '错误码',
  error_message VARCHAR(1000) NULL COMMENT '错误信息',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_llm_call_logs_record (record_id),
  KEY idx_llm_call_logs_record_created (record_id, created_at, id),
  KEY idx_llm_call_logs_config_created (llm_config_id, created_at),
  KEY idx_llm_call_logs_status_created (status, created_at),
  KEY idx_llm_call_logs_provider_model (provider, model_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='LLM调用日志';
```

### 6.3 config_audit_logs

记录 LLM 配置变更审计，不保存 API Key 明文。

```sql
CREATE TABLE config_audit_logs (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '配置审计ID',
  config_type VARCHAR(40) NOT NULL COMMENT 'llm_config/system',
  config_id BIGINT UNSIGNED NOT NULL COMMENT '配置ID',
  action VARCHAR(40) NOT NULL COMMENT 'create/update/enable/disable/test/delete',
  operator_id BIGINT UNSIGNED NOT NULL COMMENT '操作者用户ID',
  before_data JSON NULL COMMENT '变更前数据，不含明文Key',
  after_data JSON NULL COMMENT '变更后数据，不含明文Key',
  change_summary VARCHAR(500) NULL COMMENT '变更摘要',
  ip_address VARCHAR(64) NULL COMMENT '操作IP',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_config_audit_logs_config (config_type, config_id),
  KEY idx_config_audit_logs_operator_created (operator_id, created_at),
  KEY idx_config_audit_logs_action_created (action, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='配置审计日志';
```

## 7. 后台列表查询索引

- 用户管理：`users(role, status)`、`users(created_at)`。
- 用户历史记录：`generation_records(user_id, created_at)`。
- 管理端生成记录：`generation_records(status, created_at)`、`generation_records(transport_mode, created_at)`。
- 记录详情：所有子表均有 `record_id` 索引。
- 流式事件恢复：`generation_stream_events(record_id, sequence_no)` 唯一索引。
- LLM 成本统计：`llm_call_logs(llm_config_id, created_at)`、`llm_call_logs(status, created_at)`。

## 8. MVP 建表优先级

第一期必须建：

- `users`
- `login_sessions`
- `generation_records`
- `generation_inputs`
- `generation_outputs`
- `generation_stream_events`
- `generation_errors`
- `route_snapshots`
- `route_map_exports`
- `weather_snapshots`
- `news_snapshots`
- `llm_configs`
- `llm_call_logs`
- `config_audit_logs`

可以第二期再建：

- `external_api_cache`

## 9. 初始数据建议

- 初始化一个管理员用户：`username = 'admin'`，初始密码 `admin123456`，`role = 'admin'`，`status = 'active'`。
- 默认管理员密码只用于本地初始化和首次登录，入库必须保存 `password_hash`，生产环境首次部署后必须修改。
- 初始化一个禁用状态的 LLM 配置模板，管理员首次进入后台后补充 API Key 并测试启用。
- 游客生成记录也需要绑定 `users` 表中的 `guest` 用户，便于历史记录和隐私数据清理。
