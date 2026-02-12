# OPML 导入导出功能增强方案

## 现状分析

项目已具备基础的 OPML 导入功能，包括后端 `opml_service.py`（基于 `xml.etree.ElementTree` 的简单解析器）、`feeds.py` router 中的 `/api/feeds/import-opml` 端点，以及前端的 `ImportOpmlDialog` 组件。但当前实现存在以下不足：导出功能完全缺失，导入仅支持两层嵌套（分组 > feed），不保留 `htmlUrl`/`description` 等 OPML 元信息，缺少导入前的预览确认步骤，错误报告不够详细（仅返回 added/skipped/failed 的数量）。

## OPML 2.0 格式说明

OPML 2.0 是一种基于 XML 的大纲格式。在 RSS 订阅场景中，核心结构如下：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<opml version="2.0">
  <head>
    <title>RSS Reader Subscriptions</title>
    <dateCreated>Wed, 11 Feb 2026 12:00:00 GMT</dateCreated>
  </head>
  <body>
    <outline text="Technology" title="Technology">
      <outline type="rss" text="TechCrunch" title="TechCrunch"
        xmlUrl="https://feeds.techcrunch.com/TechCrunch/"
        htmlUrl="https://techcrunch.com"
        description="Breaking tech news" />
    </outline>
    <outline type="rss" text="Hacker News" title="Hacker News"
      xmlUrl="https://news.ycombinator.com/rss" />
  </body>
</opml>
```

对于 RSS 订阅的 outline 节点，`type="rss"` 且 `xmlUrl` 是必需属性，`text`/`title`、`htmlUrl`、`description` 是可选属性。不含 `xmlUrl` 的 outline 节点通常表示分组（文件夹），其子节点为实际的 feed 订阅。

不同 RSS 阅读器的导出格式存在差异：Feedly 将嵌套分类扁平化为单层（如 "Category 1 -- Sub A"），有些阅读器的 `type` 属性可能设为 `"rss"` 或 `"atom"` 或干脆不设。解析时需要宽容处理，只要有 `xmlUrl` 属性即视为有效 feed。


## 导出功能方案

### API 端点

```
GET /api/feeds/export-opml
```

返回 `Content-Type: application/xml`，`Content-Disposition: attachment; filename="subscriptions.opml"` 的 OPML 文件。

### 数据映射

从数据库 Feed 和 Group 模型映射到 OPML 结构：

Feed model field | OPML outline attribute
--- | ---
feed.title | text, title
feed.url | xmlUrl
feed.site_url | htmlUrl
feed.description | description
group.name | 父级 outline 的 text/title

没有 group 的 feed 直接放在 body 的顶层。有 group 的 feed 按 group 的 sort_order 排序后，嵌套在对应的 group outline 下。

### 后端实现

在 `opml_service.py` 中新增 `generate_opml` 函数，使用 `xml.etree.ElementTree` 构建 XML 文档。代码逻辑为：查询所有 groups（按 sort_order 排序）和所有 feeds，按 group_id 分组 feeds，依次写入分组和无分组的 feed，最后使用 `ET.tostring` 输出 XML 字符串。

在 feeds router 中新增端点，返回 `Response(content=xml_string, media_type="application/xml")`，设置合适的 Content-Disposition header。


## 导入功能增强方案

### 当前流程的问题

当前导入流程是"选文件就直接导入"，用户无法在导入前看到将要导入什么内容，也不能选择性导入。对于大量订阅（如从 Feedly 迁移几百个 feed），全部导入可能不是用户想要的。

### 增强后的两阶段导入

将导入拆分为两个 API：

第一阶段（预览）：`POST /api/feeds/preview-opml`，接收 OPML 文件，解析后返回将要导入的 feeds 和 groups 列表，标注哪些已存在（重复），不做任何数据库写入。

```json
{
  "groups": [
    {"name": "Technology", "feed_count": 5, "is_new": true},
    {"name": "News", "feed_count": 3, "is_new": false}
  ],
  "feeds": [
    {"title": "TechCrunch", "url": "https://...", "group": "Technology", "status": "new"},
    {"title": "BBC News", "url": "https://...", "group": "News", "status": "duplicate"}
  ],
  "summary": {"total": 8, "new": 5, "duplicate": 3}
}
```

第二阶段（执行导入）：保持现有 `POST /api/feeds/import-opml` 端点，但增强其返回信息，包含每个失败 feed 的具体错误原因。

### 解析增强

增强 `parse_opml` 使其保留更多属性：

```python
@dataclass
class OpmlFeed:
    title: str
    url: str           # xmlUrl
    site_url: str | None   # htmlUrl
    description: str | None
    group: str | None
```

解析逻辑需要更宽容：不依赖 `type` 属性判断是否为 feed，只要 outline 节点有 `xmlUrl` 就视为 feed。支持多层嵌套（三层以上的嵌套扁平化为 "Parent / Child" 格式的 group 名称）。处理编码问题（UTF-8 BOM、XML 声明编码不匹配等）。

### 冲突处理策略

导入时遇到重复 feed（URL 已存在）的默认行为是跳过。不需要提供"覆盖"选项，因为 feed 的核心数据（title、metadata）会在抓取时自动更新。对于 group，如果同名 group 已存在就复用，不重复创建。

### 批量创建优化

当前实现逐个创建 feed（每个 feed 都触发 HTTP 请求去解析 feed URL 获取 metadata）。对于大量导入，这会非常慢。优化方案是在导入时，如果 OPML 中已提供 title，直接使用 OPML 的 title 创建 feed 记录，将 feed URL 的解析和 metadata 获取作为后台任务异步执行。这样导入操作从"串行等待每个 feed 的 HTTP 请求"变为"批量写入数据库"，速度提升数十倍。

具体实现：新增 `create_feed_from_opml` 函数，跳过 `parse_feed_url` 步骤，直接使用 OPML 提供的 title/htmlUrl/description 创建 Feed 记录，状态设为 active。创建后由后台调度器的定期抓取任务自动补全 metadata 并获取文章。


## 前端 UI 方案

### 导入对话框增强

将现有的 `ImportOpmlDialog` 从"选文件即导入"改为两步式：

第一步（文件选择与预览）：用户选择 OPML 文件后，调用 preview API 展示将要导入的内容。UI 显示为一个按分组组织的列表，每个 feed 旁标注 "new" 或 "duplicate" 状态。提供全选/取消全选按钮（后续迭代考虑，MVP 阶段可以先不做选择性导入）。底部显示 "将导入 N 个新 feed，跳过 M 个重复" 的摘要。

第二步（确认导入）：用户点击确认后执行导入，显示进度状态，完成后展示结果。

### 导出按钮

在 sidebar 的下拉菜单中新增 "Export OPML" 选项，点击后直接触发浏览器下载。前端通过创建一个隐藏的 `<a>` 标签，设置 `href` 为 `/api/feeds/export-opml`，触发下载。不需要额外的对话框。

### 前端 API 层

在 `feeds.ts` 中新增：

```typescript
export function previewOpml(
  file: File
): Promise<OpmlPreviewResult> {
  const formData = new FormData();
  formData.append('file', file);
  return apiClient.upload<OpmlPreviewResult>('/feeds/preview-opml', formData);
}

export function exportOpml(): void {
  window.open('/api/feeds/export-opml', '_blank');
}
```


## 实现步骤

### 第一步：导出功能（后端）

在 `opml_service.py` 中新增 `generate_opml(feeds, groups)` 函数，使用 `xml.etree.ElementTree` 生成符合 OPML 2.0 规范的 XML。在 `feeds.py` router 中新增 `GET /api/feeds/export-opml` 端点，查询当前用户的所有 feeds 和 groups，调用 `generate_opml` 生成 XML 并返回。

### 第二步：导出功能（前端）

在 `SidebarFooter.tsx` 的下拉菜单中添加 "Export OPML" 按钮，使用 `<a>` 标签或 `window.open` 触发下载。在 `feeds.ts` 中添加对应的 API helper。

### 第三步：增强导入解析

修改 `opml_service.py` 中的 `OpmlFeed` dataclass，增加 `site_url` 和 `description` 字段。增强 `parse_opml` 以提取更多属性、支持多层嵌套、更宽容的格式处理。

### 第四步：预览 API

新增 `POST /api/feeds/preview-opml` 端点。该端点解析 OPML 文件，与现有 feeds 做去重比对，返回预览结果（哪些是新的、哪些是重复的）。

### 第五步：批量导入优化

新增 `create_feed_from_opml` 函数，直接使用 OPML 的 metadata 创建 feed 记录（跳过网络请求）。修改 `import_opml` 端点使用新的批量创建函数。

### 第六步：前端导入对话框增强

重构 `ImportOpmlDialog`，实现两阶段流程（选文件 -> 预览 -> 确认导入）。增强导入结果的展示（分组显示、错误详情）。


## 需要的新依赖

不需要新增依赖。现有的 `xml.etree.ElementTree`（Python 标准库）完全满足 OPML 的解析和生成需求。虽然 `listparser` 库提供了更健壮的解析能力（支持 lxml fallback、处理畸形 XML），但考虑到项目的 OPML 处理需求相对简单（标准的 RSS 订阅列表），标准库足够使用，且避免了额外依赖。如果后续遇到需要处理大量非标准 OPML 文件的情况，可以考虑引入 `listparser`。


## 设计决策说明

为什么不使用 `listparser`：项目当前使用 `xml.etree.ElementTree` 的实现已经能正确解析标准 OPML 文件。引入 `listparser` 的主要价值在于处理畸形 XML，但主流 RSS 阅读器（Feedly、Inoreader、NewsBlur 等）导出的 OPML 都是格式良好的。保持零额外依赖更符合项目简洁的风格。

为什么导入不做选择性导入（MVP 阶段）：选择性导入增加了前后端的复杂度（需要在前端维护选择状态，在后端接受 feed URL 列表），而实际使用中，用户从其他阅读器迁移时通常希望全量导入。已有重复检测能自动跳过已存在的 feed。如果用户确实需要部分导入，可以在导出前在原阅读器中整理订阅列表。

为什么导入使用 OPML metadata 而不是实时抓取：批量导入可能涉及几十到几百个 feed。如果每个 feed 都进行 HTTP 请求解析 metadata，导入时间会非常长（几分钟甚至更久），用户体验差。OPML 文件本身已经包含 title 和可选的 htmlUrl/description，这些信息足以创建 feed 记录。后续的定期抓取任务会自动补全和更新 metadata。
