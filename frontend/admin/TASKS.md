# 管理后台任务清单

## 1. 管理后台功能

- [x] 管理员登录页。
- [x] 后台首页 (统计卡片：总用户数、生成记录数、已启用 LLM 配置数)。
- [x] 用户管理 (列表、搜索、状态筛选、角色筛选、分页)。
- [x] LLM 配置管理 (列表、新建、编辑、详情)。
- [x] LLM API 地址、模型名和 API Key 表单。
- [x] API Key 掩码展示和重新填写 (编辑时留空则不修改)。
- [ ] LLM 编辑接口字段联调。负责人：FE-Admin、BE-Stream；状态：进行中；优先级：P1；说明：前端编辑会发送 `provider`，后端更新 Schema 当前不接收；编辑弹窗也需要先拉详情，避免用列表默认值覆盖 `timeout_s/max_tokens/temperature`。
- [x] LLM 连接测试按钮 (弹窗输入 Prompt，展示测试结果)。
- [x] LLM 配置启用/停用。
- [x] 生成记录列表 (分页、状态筛选、交通方式筛选、用户搜索)。
- [x] 生成记录详情 (输入参数、输出结果、错误信息、LLM 调用日志)。
- [x] 生成状态筛选。
- [x] 错误信息查看 (详情页错误表格：阶段、错误码、错误信息)。
- [x] 失败记录重试。
- [x] 调用耗时和 Token 消耗展示 (详情页 LLM 调用日志表格)。

## 2. 前端工程

- [x] 初始化管理后台 Vue 3 + Vite 工程。
- [x] 配置管理后台本地默认端口为 `3004`。
- [x] 配置管理后台 API Base URL 默认指向 `http://localhost:3002`。
- [x] 配置 Pinia。
- [x] 配置 Vue Router (含路由守卫：未登录跳转登录页、非 admin 角色拒绝访问)。
- [x] 配置 UI 组件库 (Element Plus + unplugin-vue-components 按需导入)。
- [x] 封装 request 客户端 (Axios 实例 + 统一响应解包 + 401 自动刷新)。
- [x] 按 `docs/api/frontend_backend_integration.md` 封装管理后台 API 模块 (auth + admin CRUD)。
- [x] 封装登录态 (Pinia store + localStorage 持久化 + 登录后校验 role=admin)。
- [x] 封装错误提示 (ElMessage 统一下发)。
- [x] 封装加载态和空态 (useLoading composable + el-empty + el-table v-loading)。
- [x] 配置 ESLint。
