# Git Habits Analyzer

跨仓库 Git 提交习惯分析与可视化平台。

## 技术栈

- **后端**: FastAPI + Celery + Redis + SQLite
- **前端**: React + TypeScript + ECharts + Vite
- **CLI**: Typer + GitPython + Rich
- **部署**: Docker Compose

## 项目结构

```
├── backend/              # FastAPI + Celery 后端
│   ├── app/
│   │   ├── api/          # REST API 端点
│   │   ├── cli/          # CLI 工具 (Typer)
│   │   ├── services/     # 核心业务逻辑
│   │   └── tasks/        # Celery 异步任务
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/             # React 前端
│   ├── src/
│   │   ├── components/   # ECharts 图表组件
│   │   ├── pages/        # 页面组件
│   │   └── api/          # API 客户端
│   ├── Dockerfile
│   └── package.json
└── docker-compose.yml
```

## 快速开始

### Docker Compose 部署

```bash
# 克隆仓库
git clone <repo-url>
cd 603am02

# 启动所有服务
docker-compose up --build

# 访问
# 前端: http://localhost:3000
# API:  http://localhost:8000/docs
```

### 本地开发

**后端:**

```bash
cd backend
pip install -e .

# 启动 Redis
redis-server

# 启动 API
uvicorn app.main:app --reload --port 8000

# 启动 Celery Worker
celery -A app.tasks.celery_app:celery_app worker --loglevel=info
```

**前端:**

```bash
cd frontend
npm install
npm run dev
```

### CLI 使用

```bash
cd backend

# 配置仓库 (编辑 repos.yaml)
cp repos.yaml.example repos.yaml

# 分析所有配置的仓库
python -m app.cli.main analyze --config repos.yaml

# 导出 JSON 报告
python -m app.cli.main export-json --output report.json

# 分析指定仓库
python -m app.cli.main analyze --repo my-project

# 带日期过滤
python -m app.cli.main analyze --since 2024-01-01 --until 2024-12-31

# 列出已配置仓库
python -m app.cli.main list-repos
```

## 仓库配置 (repos.yaml)

```yaml
repos:
  - name: "my-project"
    path: "/path/to/my-project"
    branch: "main"
  - name: "another-project"
    path: "/path/to/another-project"
    branch: "develop"
```

## API 端点

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/repos` | 列出所有仓库 |
| POST | `/api/repos` | 添加仓库 |
| PUT | `/api/repos/{id}` | 更新仓库配置 |
| DELETE | `/api/repos/{id}` | 删除仓库 |
| POST | `/api/analysis/trigger` | 触发异步分析 |
| GET | `/api/analysis/reports/{repo_id}` | 获取报告 |
| GET | `/api/analysis/reports/aggregate` | 跨仓库聚合统计 |
| GET | `/api/tasks/{task_id}` | 查询任务状态 |

## 功能特性

- GitHub 风格的提交热力图 (ECharts Calendar Heatmap)
- 每日/每周提交频率统计
- 代码变更量趋势 (insertions/deletions)
- 连续提交天数 (streak) 统计
- 多仓库配置与聚合分析
- 非 UTF-8 编码提交信息自动处理
- 仓库权限异常优雅处理
- Celery 异步分析 + 进度轮询
