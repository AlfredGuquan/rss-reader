# 话题聚类与去重实现计划

## 问题描述

同一新闻事件被多个 RSS 源报道时，文章列表中出现大量重复或高度相关的内容。用户需要像邮件对话视图一样，将报道同一话题的文章自动聚合在一起，减少信息噪音，提高阅读效率。

## 现有 Codebase 分析

当前 Entry 模型包含以下可用于相似度计算的字段：`title`（标题）、`url`（链接）、`summary`（摘要）、`content`（正文）、`published_at`（发布时间）。项目已有 FTS5 全文搜索索引（`entries_fts` 表，索引 title 和 content），已依赖 trafilatura（自带 SimHash 去重功能），使用 SQLite + aiosqlite 异步数据库。前端使用 `@tanstack/react-virtual` 进行虚拟列表渲染，EntryCard 组件展示标题、来源、时间和摘要。

## 技术方案对比

### 方案 A：基于 SimHash 的轻量去重（推荐首选）

核心思路是使用 trafilatura 自带的 SimHash 对文章标题和摘要生成指纹，通过 Hamming 距离判断近似重复。

优势在于零新依赖（trafilatura 已在项目中），计算极快（纯哈希运算），存储空间小（每篇文章一个 64-bit 指纹），非常适合检测转载、洗稿等"近似重复"内容。劣势是只能检测文本高度相似的文章，无法识别"同一话题但不同角度"的报道。SimHash 的相似度阈值需要调优，中文分词效果可能不如英文。

适用场景是去重——同一篇文章被多个源转载。

### 方案 B：基于 Embedding 的语义聚类

使用 sentence-transformers（如 all-MiniLM-L6-v2）生成文章的语义向量，存储在 sqlite-vec 中，通过余弦相似度进行聚类。

优势在于能理解语义相似性，可以把报道同一事件但用词不同的文章聚到一起，是 Feedly 等成熟产品的核心技术。劣势是需要引入 sentence-transformers（约 400MB 模型）和 sqlite-vec 扩展，首次生成向量需要较长时间（GPU 加速或 CPU 逐条处理），对个人 RSS 阅读器来说可能过于重量级。

适用场景是话题聚类——将报道同一事件的不同角度文章聚合。

### 方案 C：基于 LLM 的智能聚类

调用 LLM API（如 Claude、OpenAI）判断两篇文章是否报道同一事件。

优势在于准确度最高，能理解复杂语义关系。劣势是成本高（每次比较需要 API 调用），延迟大，无法离线使用，不适合大规模批量处理。

适用场景是作为辅助手段，对不确定的聚类结果进行精细判断。

### 方案 D：混合方案（推荐的最终方案）

参考 Feedly 的架构，采用分层处理策略。第一层用 SimHash 快速去重，过滤掉 80% 的近似重复内容。第二层用标题 TF-IDF + 余弦相似度做轻量聚类，将明显相关的文章归组。第三层（可选）用 Embedding 做语义聚类，处理第二层遗漏的关联文章。

这种分层方法的核心参考来自 Feedly 的工程博客：他们发现 80% 的文章是重复的，先去重后聚类可以将工作量缩减到 1/5。

## 推荐的分阶段实现方案

### 阶段一：SimHash 快速去重（最小可行方案）

目标是消除近似重复文章，将重复内容折叠为"N 个源报道了此新闻"。

后端实现包括：在 Entry 模型新增 `simhash_title` 字段（VARCHAR 16，存储标题的 SimHash 指纹）和 `simhash_content` 字段（VARCHAR 16，存储内容指纹）以及 `duplicate_of_id` 字段（UUID，指向原始文章的外键，NULL 表示非重复）。在文章入库时（`fetch_service.py`），使用 trafilatura 的 `content_fingerprint()` 计算指纹，与同一时间窗口（如 ±3 天）内的已有文章比较 SimHash 相似度，如果标题相似度 > 0.85 则标记为重复（设置 `duplicate_of_id`）。新增 `/api/entries` 查询参数 `deduplicate=true`，返回结果时折叠重复文章。

前端实现包括：在 EntryCard 组件中，如果文章有重复项，显示"N 个源"的标记。点击可以展开查看所有来源。在 EntryFilterBar 中添加"去重"开关。

关键代码示例：

```python
# backend/app/services/dedup_service.py
from trafilatura.deduplication import Simhash, content_fingerprint

TITLE_SIMILARITY_THRESHOLD = 0.85
TIME_WINDOW_DAYS = 3

async def compute_simhash(entry: Entry) -> str:
    """计算文章标题的 SimHash 指纹"""
    return content_fingerprint(entry.title or "")

async def find_duplicate(
    db: AsyncSession, entry: Entry, user_id: uuid.UUID
) -> uuid.UUID | None:
    """在时间窗口内查找近似重复文章"""
    new_hash = Simhash(entry.title or "")
    cutoff = entry.published_at - timedelta(days=TIME_WINDOW_DAYS)

    stmt = (
        select(Entry.id, Entry.simhash_title)
        .join(Feed, Entry.feed_id == Feed.id)
        .where(
            Feed.user_id == user_id,
            Entry.published_at >= cutoff,
            Entry.simhash_title.isnot(None),
            Entry.duplicate_of_id.is_(None),  # 只与"原始"文章比较
        )
    )
    result = await db.execute(stmt)
    for row in result.all():
        existing_hash = Simhash(existing_hash=int(row.simhash_title, 16))
        if new_hash.similarity(existing_hash) >= TITLE_SIMILARITY_THRESHOLD:
            return row.id
    return None
```

### 阶段二：标题 TF-IDF 话题聚类

目标是将报道同一事件但文本不完全相同的文章聚合为"话题"。

后端实现包括：新增 `topic_clusters` 表（`id`, `title`, `representative_entry_id`, `entry_count`, `created_at`, `updated_at`）和 `entry_cluster_map` 表（`entry_id`, `cluster_id`，多对多关系，一篇文章可能属于多个话题）。实现基于 TF-IDF + 余弦相似度的增量聚类服务：新文章入库时，提取标题的 TF-IDF 向量，与最近 N 天内的聚类中心比较，如果最高相似度 > 阈值则加入该聚类，否则创建新聚类。依赖 scikit-learn 的 `TfidfVectorizer` 和 `cosine_similarity`，这是一个轻量级依赖。

新增 API endpoint `/api/topics`，返回话题列表，每个话题包含代表文章和相关文章数量。

前端实现包括：新增"话题视图"模式（与现有列表视图并列），话题卡片展示代表文章标题、来源数量、时间范围，点击话题展开查看所有相关文章，按来源和时间排序。

聚类策略使用增量式单遍聚类（single-pass clustering），而非传统的批量 DBSCAN，因为 RSS 阅读器的文章是流式到达的。核心逻辑是：维护一个活跃聚类列表（最近 N 天），每个聚类保存其中心向量（所有成员标题 TF-IDF 的平均值）。新文章到达时，计算与所有活跃聚类中心的余弦相似度。如果最高相似度超过阈值（如 0.4），加入该聚类并更新中心向量。否则为这篇文章创建新的单文章聚类。

```python
# backend/app/services/clustering_service.py
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

CLUSTER_SIMILARITY_THRESHOLD = 0.4
CLUSTER_WINDOW_DAYS = 7

class TopicClusteringService:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',  # 可扩展中文停用词
            ngram_range=(1, 2),
        )
        self._fitted = False

    async def assign_cluster(
        self, db: AsyncSession, entry: Entry, user_id: uuid.UUID
    ) -> uuid.UUID | None:
        """为新文章分配话题聚类"""
        # 获取活跃聚类的代表标题
        active_clusters = await self._get_active_clusters(db, user_id)
        if not active_clusters:
            return await self._create_cluster(db, entry)

        # 计算相似度
        titles = [c.title for c in active_clusters] + [entry.title]
        tfidf_matrix = self.vectorizer.fit_transform(titles)
        similarities = cosine_similarity(
            tfidf_matrix[-1:], tfidf_matrix[:-1]
        )[0]

        max_idx = np.argmax(similarities)
        if similarities[max_idx] >= CLUSTER_SIMILARITY_THRESHOLD:
            return await self._add_to_cluster(
                db, entry, active_clusters[max_idx].id
            )
        return await self._create_cluster(db, entry)
```

### 阶段三：Embedding 语义聚类（可选进阶）

目标是捕获语义层面的关联，处理翻译内容、不同表述的同一事件。

实现方式是引入 sqlite-vec 扩展和 sentence-transformers，在文章入库时生成 384 维向量并存储。使用 `vec_distance_cosine()` 进行近邻查询。这一阶段的实现可以作为阶段二的增强而非替代。当 TF-IDF 聚类不确定时（相似度在 0.3-0.4 的灰色地带），使用 Embedding 做二次确认。

新增依赖：`sqlite-vec>=0.1.6`、`sentence-transformers>=3.0.0`。

```python
# 向量存储 schema
"""
CREATE VIRTUAL TABLE entry_embeddings USING vec0(
    entry_id TEXT PRIMARY KEY,
    title_embedding float[384]
);
"""
```

## 数据模型扩展

### 阶段一新增字段（Entry 表）

```sql
ALTER TABLE entries ADD COLUMN simhash_title VARCHAR(16);
ALTER TABLE entries ADD COLUMN simhash_content VARCHAR(16);
ALTER TABLE entries ADD COLUMN duplicate_of_id UUID REFERENCES entries(id);
CREATE INDEX ix_entries_simhash_title ON entries(simhash_title);
CREATE INDEX ix_entries_duplicate_of ON entries(duplicate_of_id);
```

### 阶段二新增表

```sql
CREATE TABLE topic_clusters (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    title VARCHAR NOT NULL,          -- 聚类的代表标题
    representative_entry_id UUID REFERENCES entries(id),
    entry_count INTEGER DEFAULT 1,
    first_seen_at TIMESTAMP NOT NULL,
    last_seen_at TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,  -- 超过 N 天未更新则置为 FALSE
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE entry_cluster_map (
    entry_id UUID NOT NULL REFERENCES entries(id) ON DELETE CASCADE,
    cluster_id UUID NOT NULL REFERENCES topic_clusters(id) ON DELETE CASCADE,
    similarity_score REAL,           -- 加入时的相似度分数
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (entry_id, cluster_id)
);

CREATE INDEX ix_topic_clusters_user_active
    ON topic_clusters(user_id, is_active);
CREATE INDEX ix_topic_clusters_last_seen
    ON topic_clusters(last_seen_at);
```

### 阶段三新增虚拟表

```sql
CREATE VIRTUAL TABLE entry_embeddings USING vec0(
    entry_id TEXT PRIMARY KEY,
    title_embedding float[384]
);
```

## 前端展示方案

### 去重模式（阶段一）

在现有文章列表中，重复文章被折叠。EntryCard 组件增加一个"来源徽章"区域，显示"被 N 个源报道"。用户点击徽章后展开查看所有来源，每个来源显示 favicon、名称和发布时间。用户可以选择查看任意来源的版本。在 EntryFilterBar 添加"自动去重"开关，默认开启。

```tsx
// 新增类型
interface Entry {
  // ... 现有字段
  duplicate_of_id?: string | null;
  duplicate_count?: number;      // 此文章的重复数
  duplicate_sources?: Array<{    // 重复来源列表
    entry_id: string;
    feed_title: string;
    feed_favicon_url: string;
    published_at: string;
  }>;
}
```

### 话题视图（阶段二）

新增"话题"视图模式，与现有"文章"视图并列，通过 Tab 切换。话题卡片设计包括：代表文章标题（最早或最高质量来源的标题），来源数量角标（如"5 篇报道"），时间范围（从最早到最新），展开后显示该话题下所有文章的紧凑列表。

```tsx
interface TopicCluster {
  id: string;
  title: string;
  representative_entry: Entry;
  entry_count: number;
  first_seen_at: string;
  last_seen_at: string;
  entries?: Entry[];  // 展开时加载
}
```

API 设计：

```
GET /api/topics?page=1&per_page=20&status=all
GET /api/topics/{topic_id}/entries
```

## 性能考量

### 阶段一性能

SimHash 计算：每篇文章 < 1ms，纯 CPU 计算无压力。去重查询：需要遍历时间窗口内的文章指纹进行 Hamming 距离比较。对于 1000 篇文章约需 5-10ms（SimHash 比较是 O(1) 的位运算）。通过 `simhash_title` 索引可以快速缩小候选范围。瓶颈不在计算而在 I/O，建议在 fetch_service 的文章入库流程中同步完成，不需要额外的后台任务。

### 阶段二性能

TF-IDF 向量化：对 1000 个标题约需 50-100ms。余弦相似度计算：与 100 个活跃聚类比较约需 10-20ms。关键优化：不要对全部历史文章做全量聚类，只维护最近 N 天的活跃聚类。TfidfVectorizer 需要重新 fit（因为词汇表会变化），可以定期（如每小时）重建，中间使用缓存的向量。对于个人 RSS 阅读器（每天几十到几百篇新文章）的规模，这些开销完全可以接受。

### 阶段三性能

Embedding 生成：all-MiniLM-L6-v2 在 CPU 上约 10-50ms/篇（取决于文本长度）。sqlite-vec 近邻查询：对 10000 个向量的 KNN 查询约需 20-50ms。主要瓶颈是首次对历史文章批量生成 Embedding，可作为一次性迁移任务在后台运行。

## 具体实现步骤

### 阶段一实施步骤（预估 1-2 天）

1. 创建 Alembic 迁移，为 entries 表添加 `simhash_title`、`simhash_content`、`duplicate_of_id` 字段和索引。

2. 创建 `backend/app/services/dedup_service.py`，实现 `compute_simhash()`、`find_duplicate()` 函数。

3. 修改 `backend/app/services/fetch_service.py`，在新文章入库时调用去重逻辑。

4. 创建一次性脚本，为已有文章计算 SimHash 指纹并检测重复。

5. 修改 `backend/app/routers/entries.py` 的 `list_entries` endpoint，支持 `deduplicate` 参数，折叠重复文章并返回重复计数。

6. 修改前端 `EntryCard.tsx`，增加重复来源的展示逻辑。

7. 修改前端 `EntryFilterBar.tsx`，添加去重开关。

8. 修改前端 `types/index.ts`，扩展 Entry 类型。

### 阶段二实施步骤（预估 2-3 天）

1. 添加 `scikit-learn` 依赖到 `pyproject.toml`。

2. 创建 Alembic 迁移，新增 `topic_clusters` 和 `entry_cluster_map` 表。

3. 创建 `backend/app/models/topic_cluster.py` 定义 ORM 模型。

4. 创建 `backend/app/services/clustering_service.py`，实现增量聚类逻辑。

5. 修改 fetch_service，在去重后对非重复文章执行聚类。

6. 创建 `backend/app/routers/topics.py`，实现话题列表和详情 API。

7. 创建一次性脚本，对已有文章进行批量聚类。

8. 前端新增 TopicClusterCard 组件和话题视图页面。

9. 添加视图切换 UI（文章视图 / 话题视图）。

### 阶段三实施步骤（预估 2-3 天，可选）

1. 添加 `sqlite-vec` 和 `sentence-transformers` 依赖。

2. 创建 Alembic 迁移，初始化 vec0 虚拟表。

3. 在 database.py 中加载 sqlite-vec 扩展。

4. 创建 `backend/app/services/embedding_service.py`，封装 Embedding 生成和查询。

5. 修改聚类服务，在 TF-IDF 不确定时使用 Embedding 二次确认。

6. 创建批量 Embedding 生成脚本。

## 需要的新依赖

### 阶段一

无新依赖（trafilatura 已包含 SimHash 功能）。

### 阶段二

`scikit-learn>=1.5.0`（约 30MB，提供 TF-IDF 和余弦相似度计算）。

### 阶段三

`sqlite-vec>=0.1.6`（SQLite 向量搜索扩展，纯 C 实现，非常轻量），`sentence-transformers>=3.0.0`（需要 PyTorch，约 400MB+ 的模型下载）。

## 总结

推荐从阶段一开始实施。SimHash 去重是零成本、高回报的方案，利用项目已有的 trafilatura 依赖，无需引入任何新包。根据 Feedly 的数据，约 80% 的重复内容可以通过这一步消除。阶段二的 TF-IDF 聚类是性价比最高的话题聚合方案，scikit-learn 是一个成熟稳定的轻量依赖。阶段三的 Embedding 方案作为锦上添花，只在用户需要更精准的语义理解时才引入。
