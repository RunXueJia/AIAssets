# 24小时AI增长资产引擎文档索引

版本：v1.1  
日期：2026-05-19  
依据文档：PROJECT_REQUIREMENTS.md  
开发模式：前后端分离  

## 1. 文档拆分

本项目文档按前后端分离方式维护：

- [PROJECT_REQUIREMENTS.md](PROJECT_REQUIREMENTS.md)：项目需求说明。
- [FRONTEND_TASKS.md](FRONTEND_TASKS.md)：前端任务清单，面向 Vue 3 + Vite 后台开发。
- [BACKEND_TASKS.md](BACKEND_TASKS.md)：后端任务清单，面向 Python + FastAPI + MySQL 开发。
- [API_INTEGRATION_TASKS.md](API_INTEGRATION_TASKS.md)：前后端接口、SSE、联调和交付约定。

## 2. 前后端分离约束

本项目必须采用前后端分离架构。

- 前端和后端是两个独立项目。
- 前端使用 Vue 3 + Vite，只负责页面、交互、路由、状态和接口调用。
- 后端使用 Python + FastAPI，只负责 API、SSE、数据库、任务队列、抓取、LLM、视频合成和文件服务。
- 前端不直接连接 MySQL、Redis、对象存储或文件目录。
- 后端不渲染 Vue 页面，不写 Jinja/HTML 后台模板。
- 前后端只通过 HTTP API、SSE 和文件下载接口通信。
- 前端可以通过 mock 数据独立开发。
- 后端接口不依赖前端实现，可以用 Swagger/Postman 独立调试。
- 前端和后端独立启动、独立构建、独立部署。
- 鉴权统一使用 Token，前端只保存 Token，权限判断以后端为准。
- 跨域由后端 CORS 或 Nginx 反向代理处理。

## 3. 推荐目录

```text
hours24/
  PROJECT_REQUIREMENTS.md
  FRONTEND_BACKEND_TASKS.md
  FRONTEND_TASKS.md
  BACKEND_TASKS.md
  API_INTEGRATION_TASKS.md
  frontend/
    admin/
  backend/
    api/
    worker/
    renderer/
  storage/
    videos/
    covers/
    cards/
    downloads/
    publish-packages/
  deploy/
    nginx/
    docker/
```

## 4. MVP 优先级

P0 必须完成：

- 登录和权限。
- 内容生成入口。
- 生成任务创建。
- 网络抓取。
- 素材汇总。
- LLM 生成选题、脚本、分镜、字幕。
- SSE 流式输出。
- 审核列表。
- 视频合成。
- 发布包导出。

P1 建议完成：

- 话题监控与自动任务。
- 发布链接回填。
- 数据看板。
- 每日报告。
- 文件权限控制。

P2 后续优化：

- 更细角色权限。
- 更丰富视频模板。
- 更多抓取来源。
- 自动质量评分。
- 发布平台 API 对接。
- 公开前台网站。
