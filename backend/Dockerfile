FROM python:3.13-slim

WORKDIR /app

# 安装 uv 包管理器
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 先复制依赖文件以利用 Docker 缓存层
COPY pyproject.toml uv.lock ./

# 安装生产依赖
RUN uv sync --frozen --no-dev

# 复制应用代码
COPY app/ app/
COPY migrations/ migrations/
COPY alembic.ini .
COPY main.py .

# 创建 SQLite 数据目录
RUN mkdir -p /data

# 环境变量前缀为 RSS_，与 config.py 中 env_prefix = "RSS_" 对应
ENV RSS_DATABASE_URL=sqlite+aiosqlite:////data/rss_reader.db
ENV RSS_CORS_ORIGINS='["*"]'

EXPOSE 8000

# 启动前运行 Alembic 迁移，确保数据库 schema 是最新的
CMD ["sh", "-c", "uv run alembic upgrade head && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000"]
