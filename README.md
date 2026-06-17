# Agent Notify

一个 Claude Code / Codex CLI 的响应完成通知钩子，提供 Web UI 界面查看对话历史记录。

**📖 完整安装教程**: 请查看 [docs/QUICK-START.md](docs/QUICK-START.md) 快速上手！

## 功能

- **实时通知**：当 Claude/Codex 完成响应时，自动打开 Web UI 显示结果
- **历史记录**：SQLite 永久存储所有对话历史，支持分页浏览
- **搜索过滤**：按时间、代理、项目、分类筛选记录
- **Markdown 预览**：支持渲染 Markdown 或查看原始文本
- **数据管理**：清理旧数据、导出 CSV/JSON
- **Token 统计**：显示模型和 token 使用量
- **🆕 Windows 桌面应用**：完整 Electron 应用，系统托盘集成

## 安装

### 方式 1: Web UI（推荐）

适合 Linux/Mac 或已安装 Python 的环境。

### 1. 克隆仓库

```bash
git clone https://github.com/<your-username>/agent-notify.git
cd agent-notify
```

### 2. 配置 Claude Code Hook

在 `~/.claude/settings.json` 中添加：

```json
{
  "hooks": {
    "Stop": [
      {
        "command": "python3",
        "args": ["-m", "agent_notify.notify"]
      }
    ]
  }
}
```

### 3. 启动 Web Server

```bash
# 手动启动
python3 -m agent_notify.server

# 或使用启动脚本
bash bin/start-server.sh
```

Web UI 地址：http://localhost:18865

### 方式 2: Windows 桌面应用

适合 Windows 用户，提供完整桌面体验。

#### 构建 Windows 应用

```bash
cd desktop

# 安装依赖
npm install

# 开发运行
npm start

# 构建安装包
npm run build
# 输出: dist/Agent Notify Setup 1.0.0.exe

# 构建便携版
npm run build-portable
# 输出: dist/AgentNotify-Portable.exe
```

#### 桌面应用特性

- ✅ 系统托盘图标
- ✅ 双击托盘打开界面
- ✅ 右键菜单控制
- ✅ 关闭窗口隐藏到托盘
- ✅ 后台自动启动 Python 服务
- ✅ Windows 安装包 + 便携版

详见：`desktop/README.md`

## 项目结构

```
agent-notify/
├── agent_notify/          # Python 模块
│   ├── notify.py          # Hook 处理器
│   ├── server.py          # HTTP 服务器
│   ├── storage.py         # SQLite 存储
│   └── desktop.py         # 桌面通知
├── web/                   # Web UI
│   ├── index.html         # 主页面
│   ├── app.js             # JavaScript
│   └── styles.css         # 样式
├── desktop/               # Electron 桌面应用
│   ├── package.json       # npm 配置
│   ├── main.js            # 主进程
│   ├── preload.js         # 预加载脚本
│   ├── build.sh           # 构建脚本 (Linux/Mac)
│   ├── build.ps1          # 构建脚本 (Windows)
│   └── README.md          # 桌面应用说明
├── bin/                   # 启动脚本
│   ├── start-server.sh
│   └── monitor-server.sh  # 服务监控
├── state/                 # 数据存储（自动生成）
└── tests/                 # 测试
```

## 使用

每次 Claude Code 完成对话后，钩子会自动：
1. 记录对话内容到 SQLite 数据库
2. 在浏览器中打开 Web UI 显示最新对话

### Codex Windows App

Codex Windows app 的回答完成事件不会触发 WSL 里的 `~/.codex/hooks.json`。如果你在 Codex Windows app 中工作，请额外启动 Desktop session watcher：

```bash
bash bin/watch-codex-desktop.sh
```

它会监听 `/mnt/c/Users/xilig/.codex/sessions` 下的新 `final_answer` / `task_complete` 记录，并复用同一套 SQLite、通知 flag 和 Web UI。

首次启动时 watcher 只会把已有历史记录标记为已见，避免把旧会话全部弹出来。需要导入历史时，手动运行：

```bash
bash bin/watch-codex-desktop.sh --once --backfill
```

### Web UI 功能

- **最新对话卡片**：显示最近一次对话的完整内容
- **历史记录表格**：分页浏览所有历史
- **搜索**：关键词搜索对话内容
- **过滤**：按时间范围、代理类型、项目筛选
- **复制**：一键复制用户输入或 AI 回复
- **预览模式**：切换 Markdown 渲染 / 原始文本
- **放大查看**：弹出大窗口查看长文本
- **数据管理**：清理超过指定天数的数据
- **导出**：导出 CSV 或 JSON 格式

## 界面预览

![Web UI](docs/screenshot.png)

## 📚 文档

- **[快速开始](docs/QUICK-START.md)** - 3 分钟快速安装指南 ⭐
- **[完整教程](docs/INSTALLATION-GUIDE.md)** - 详细安装步骤和配置
- **[常见问题](docs/FAQ.md)** - 21+ 问题解答
- **[桌面应用](desktop/README.md)** - Windows 桌面应用说明

## 技术栈

- Python 3.10+
- SQLite（无限制历史存储）
- Vanilla JavaScript（无框架）
- Terminal 风格 CSS

## License

MIT
