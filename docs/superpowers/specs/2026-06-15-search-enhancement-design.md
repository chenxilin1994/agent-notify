# Agent Notify - 搜索增强功能设计文档

**日期**: 2026-06-15
**模块**: 搜索增强（标签系统 + 高亮显示）

---

## 概述

为 agent-notify 添加搜索增强功能，包括：
- 自动分类（关键词规则 + Agent 行为推断）
- 手动标签系统（Web UI 批量管理）
- 搜索结果高亮显示

---

## Part 1: 数据库结构

### 1.1 events 表新增字段

```sql
ALTER TABLE events ADD COLUMN auto_category TEXT;
ALTER TABLE events ADD COLUMN highlight_data TEXT;
```

### 1.2 tags 表（新建）

```sql
CREATE TABLE tags (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    color TEXT DEFAULT '#7b61ff',
    usage_count INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

### 1.3 event_tags 表（新建，关联表）

```sql
CREATE TABLE event_tags (
    event_id TEXT NOT NULL,
    tag_id TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (event_id, tag_id),
    FOREIGN KEY (event_id) REFERENCES events(id),
    FOREIGN KEY (tag_id) REFERENCES tags(id)
);
```

### 1.4 category_rules 表（新建，分类规则配置）

```sql
CREATE TABLE category_rules (
    id TEXT PRIMARY KEY,
    category TEXT NOT NULL,
    keywords TEXT,  -- JSON数组
    tools TEXT,     -- JSON数组
    priority INTEGER DEFAULT 0,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

---

## Part 2: 自动分类规则

### 2.1 默认分类配置

| 分类 | 关键词 | 工具 | 颜色 |
|------|--------|------|------|
| 调试 | bug, fix, error, exception, debug, 修复, 错误 | Bash (grep, cat) | #ff6b6b |
| 代码 | refactor, implement, add, create, write, 代码, 实现 | Write, Edit | #00ffa3 |
| 文档 | document, readme, doc, explain, 说明, 文档 | Read (md files) | #00d4ff |
| 阅读 | read, check, understand, 查看, 理解, 分析 | Read | #7b61ff |
| 执行 | run, test, build, deploy, 运行, 测试, 构建 | Bash, TaskCreate | #ffd700 |
| 探索 | search, find, explore, 搜索, 查找, 探索 | Glob, Grep | #00ced1 |

### 2.2 分类逻辑

1. Hook 触发时分析对话内容
2. 关键词匹配：扫描 user_input + summary
3. 工具检测：从 transcript 解析工具调用
4. 合并结果，按优先级选择最高匹配
5. 存入 events.auto_category

---

## Part 3: Web UI 功能

### 3.1 控制面板新增

- CATEGORY 筛选下拉框
- TAGS 多选筛选下拉框

### 3.2 History Log 表格新增

- CATEGORY 列：显示自动分类（带颜色徽章）
- TAGS 列：显示手动标签（可点击编辑）

### 3.3 标签管理面板

点击表格行弹出标签编辑面板：
- 显示当前标签
- 添加新标签输入框
- 常用标签快捷按钮
- 保存/取消操作

### 3.4 标签云页面

独立页面展示：
- 标签使用频率可视化
- 标签管理操作（编辑/删除/合并）

---

## Part 4: 高亮显示功能

### 4.1 高亮类型

| 类型 | 触发条件 | 颜色 |
|------|----------|------|
| 搜索匹配 | 用户输入搜索词 | 黄色 #ffd700 |
| 分类关键词 | 匹配分类规则关键词 | 对应分类颜色 |
| 标签关键词 | 包含标签名称 | 标签颜色 |

### 4.2 实现

- Hook 时预处理，存入 highlight_data (JSON)
- Web UI 渲染时正则匹配替换文本
- CSS 类控制样式

---

## Part 5: API & 导出功能

### 5.1 新增 API 接口

| 接口 | 方法 | 功能 |
|------|------|------|
| /api/tags | GET | 获取所有标签 |
| /api/tags | POST | 创建新标签 |
| /api/tags/:id | PUT | 更新标签 |
| /api/tags/:id | DELETE | 删除标签 |
| /api/events/:id/tags | GET | 获取对话标签 |
| /api/events/:id/tags | POST | 添加标签 |
| /api/events/:id/tags/:tag_id | DELETE | 移除标签 |
| /api/categories | GET | 获取分类规则 |
| /api/categories/:id | PUT | 更新分类规则 |
| /api/export/csv | GET | 导出 CSV |
| /api/export/json | GET | 导出 JSON |

### 5.2 导出功能

- CSV 格式导出
- JSON 格式导出
- 可选择导出范围（当前筛选/全部）
- 可选择包含字段

---

## 实现优先级

1. 数据库结构更新
2. 自动分类逻辑实现
3. API 接口开发
4. Web UI 功能开发
5. 高亮功能实现
6. 导出功能实现
7. 标签云页面开发

---

## 文件改动预估

| 文件 | 改动 |
|------|------|
| storage.py | 新增表、查询函数 |
| notify.py | 新增自动分类逻辑 |
| server.py | 新增 API 接口 |
| app.js | 新增 UI 功能、高亮逻辑 |
| styles.css | 新增样式 |
| index.html | 新增 UI 元素 |