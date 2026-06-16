# Agent Notify 安装教程

为 Claude Code / Codex CLI 提供响应完成通知和历史记录管理的完整指南。

---

## 📖 目录

1. [简介](#简介)
2. [安装方式](#安装方式)
3. [Web UI 版本安装](#web-ui-版本安装)
4. [Windows 桌面应用安装](#windows-桌面应用安装)
5. [配置 Claude Code Hook](#配置-claude-code-hook)
6. [使用说明](#使用说明)
7. [常见问题](#常见问题)

---

## 简介

### 什么是 Agent Notify？

Agent Notify 是一个 Claude Code/Codex CLI 的通知钩子，提供：

- **实时通知**：AI 完成响应时自动打开界面显示结果
- **历史记录**：永久存储所有对话历史（SQLite）
- **Web UI**：美观的终端风格界面
- **桌面应用**：Windows 系统托盘应用（可选）
- **搜索过滤**：按时间、代理、项目筛选
- **Markdown 预览**：渲染 Markdown 或查看原始文本
- **数据管理**：清理、导出 CSV/JSON
- **Token 统计**：模型和 token 使用量分析

### 适用人群

- Claude Code 用户（需要记录对话历史）
- Codex CLI 用户
- 开发者（需要追踪 AI 交互）
- 团队协作（共享 AI 使用记录）

---

## 安装方式

有两种安装方式，选择适合你的：

| 方式 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| **Web UI** | 跨平台、简单、无需编译 | 需要手动启动服务器 | Linux/Mac/Windows 用户 |
| **桌面应用** | 系统托盘、自动启动、GUI体验 | 仅支持 Windows | Windows 用户 |

---

## Web UI 版本安装

### 方式 1: 从 GitHub 安装（推荐）

#### 1. 克隆仓库

```bash
# 使用 HTTPS
git clone https://github.com/chenxilin1994/agent-notify.git

# 或使用 SSH
git clone git@github.com:chenxilin1994/agent-notify.git

# 进入项目目录
cd agent-notify
```

#### 2. 检查 Python 环境

```bash
# 确保 Python 3.10+ 已安装
python3 --version  # Linux/Mac
python --version   # Windows

# 如果没有安装：
# - Ubuntu/Debian: sudo apt install python3
# - Mac: brew install python3
# - Windows: https://www.python.org/downloads/
```

#### 3. 启动 Web Server

```bash
# 方式 A: 直接启动
python3 -m agent_notify.server

# 方式 B: 使用启动脚本（Linux/Mac）
bash bin/start-server.sh

# 方式 C: Windows PowerShell
python -m agent_notify.server
```

服务器将启动在：**http://localhost:18865**

#### 4. 验证安装

打开浏览器访问：
- **主页**: http://localhost:18865
- **API**: http://localhost:18865/api/stats

如果看到 JSON 数据，说明安装成功！

---

### 方式 2: 配置自动启动（可选）

#### Linux/Mac (cron)

```bash
# 编辑 crontab
crontab -e

# 添加以下行（每分钟检查服务器）
* * * * * /home/你的用户名/.local/share/agent-notify/bin/monitor-server.sh

# 或使用 systemd（推荐）
sudo nano /etc/systemd/system/agent-notify.service
```

systemd 服务文件：

```ini
[Unit]
Description=Agent Notify Server
After=network.target

[Service]
Type=simple
User=你的用户名
WorkingDirectory=/home/你的用户名/.local/share/agent-notify
ExecStart=/usr/bin/python3 -m agent_notify.server 18865
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# 启动服务
sudo systemctl daemon-reload
sudo systemctl enable agent-notify
sudo systemctl start agent-notify
```

#### Windows (任务计划程序)

```powershell
# 创建启动脚本
cd %USERPROFILE%\agent-notify
echo python -m agent_notify.server > start-server.bat

# 创建计划任务
schtasks /create /tn "AgentNotify" /tr "python -m agent_notify.server" /sc onstart /rl highest
```

---

## Windows 桌面应用安装

### 前置要求

1. **Node.js**: https://nodejs.org/ (LTS 版本推荐)
2. **Python 3**: https://www.python.org/downloads/
3. **Git**: https://git-scm.com/

### 安装步骤

#### 1. 克隆仓库

```powershell
# PowerShell
git clone https://github.com/chenxilin1994/agent-notify.git
cd agent-notify\desktop
```

#### 2. 安装依赖

```powershell
# 安装 npm 依赖
npm install

# 这会安装：
# - Electron 28.0.0
# - electron-builder 24.9.1
# - 其他构建工具
```

#### 3. 构建应用

```powershell
# 构建安装包版本
npm run build

# 输出文件：
# dist\Agent Notify Setup 1.0.0.exe (安装包)

# 或构建便携版
npm run build-portable

# 输出文件：
# dist\AgentNotify-Portable.exe (单文件)
```

#### 4. 安装使用

**安装版**：
```powershell
# 双击运行
dist\Agent Notify Setup 1.0.0.exe

# 选择安装目录
# 安装完成后自动创建桌面快捷方式
```

**便携版**：
```powershell
# 直接运行（无需安装）
dist\AgentNotify-Portable.exe

# 可放在任何位置
# 适合U盘携带或临时使用
```

### 桌面应用功能

- ✅ 系统托盘图标（右下角）
- ✅ 双击托盘打开界面
- ✅ 右键菜单控制（启动/停止/退出）
- ✅ 关闭窗口隐藏到托盘
- ✅ 自动启动 Python 服务器
- ✅ 开机自启（安装版）

---

## 配置 Claude Code Hook

### 方式 1: 手动配置

编辑 Claude Code 配置文件：

```bash
# Linux/Mac
nano ~/.claude/settings.json

# Windows PowerShell
notepad $env:USERPROFILE\.claude\settings.json
```

添加以下配置：

```json
{
  "hooks": {
    "Stop": [
      {
        "command": "python3",
        "args": [
          "-m",
          "agent_notify.notify",
          "--project-dir",
          "/home/你的用户名/.local/share/agent-notify"
        ]
      }
    ]
  }
}
```

**Windows 配置**：

```json
{
  "hooks": {
    "Stop": [
      {
        "command": "python",
        "args": [
          "-m",
          "agent_notify.notify",
          "--project-dir",
          "C:\\Users\\你的用户名\\agent-notify"
        ]
      }
    ]
  }
}
```

### 方式 2: 使用配置脚本

```bash
# Linux/Mac
cd agent-notify
python3 scripts/install-hook.py

# Windows
cd agent-notify
python scripts\install-hook.py
```

### 验证 Hook 配置

```bash
# 运行一次 Claude Code
claude

# 执行一个简单任务
> "帮我写一个 Hello World Python 程序"

# 任务完成后，检查 Web UI 是否自动打开
# 如果自动打开，说明 Hook 配置成功！
```

---

## 使用说明

### Web UI 功能

访问 http://localhost:18865

#### 主界面

- **最新对话卡片**：显示最近一次对话完整内容
- **历史记录表格**：分页浏览所有历史
- **搜索栏**：关键词搜索对话内容
- **过滤选项**：时间范围、代理类型、项目

#### 操作按钮

- **复制**：一键复制用户输入或 AI 回复
- **预览模式**：切换 Markdown 渲染 / 原始文本
- **放大查看**：弹出大窗口查看长文本
- **删除**：删除单条记录

#### 数据管理

- **清理数据**：删除超过 N 天的数据
- **导出 CSV**：导出为 CSV 文件
- **导出 JSON**：导出为 JSON 文件

#### 统计信息

- **总记录数**：历史对话总数
- **代理统计**：Claude/Codex 使用次数
- **项目统计**：各项目使用频率
- **时间统计**：最近 7/30/90/365 天数据

### 桌面应用使用

#### 系统托盘

- **图标**：绿色 = 运行中
- **双击**：打开主界面
- **右键菜单**：
  - 打开界面
  - 重启服务
  - 查看日志
  - 退出

#### 快捷键

- `Ctrl+R` - 刷新页面
- `Ctrl+W` - 隐藏窗口（不退出）
- `Esc` - 隐藏窗口

---

## 常见问题

### Q1: 服务器启动失败

**错误**: `Address already in use`

**解决**:
```bash
# 检查端口占用
lsof -i :18865  # Linux/Mac
netstat -ano | findstr :18865  # Windows

# 更改端口（如果冲突）
python3 -m agent_notify.server 28865
# 然后修改 main.js 中的 PORT
```

### Q2: Hook 不触发

**检查清单**:

1. `~/.claude/settings.json` 是否存在？
2. JSON 格式是否正确？
3. Python 路径是否正确？`python3` vs `python`
4. `agent_notify.notify` 模块是否可导入？

**调试**:
```bash
# 测试 Hook 模块
python3 -m agent_notify.notify

# 查看日志
tail -f /tmp/agent-notify.log
```

### Q3: 数据库错误

**错误**: `Database locked` 或 `No such table`

**解决**:
```bash
# 检查数据库文件
ls -la agent_notify/state/events.db

# 如果损坏，删除重建
rm agent_notify/state/events.db
python3 -m agent_notify.server  # 自动重建
```

### Q4: Windows 桌面应用无法启动

**检查**:
1. Node.js 是否安装？`node -v`
2. Python 是否在 PATH 中？`python --version`
3. 防火墙是否阻止？

**解决**:
```powershell
# 重新安装依赖
npm install --force

# 手动启动调试
npm start
```

### Q5: Electron 构建失败

**错误**: `electron-builder` 下载失败

**解决**:
```powershell
# 设置镜像源
$env:ELECTRON_MIRROR="https://npmmirror.com/mirrors/electron/"
npm run build
```

### Q6: 如何更新版本

```bash
# Web UI 版本
cd agent-notify
git pull origin main

# 桌面应用版本
cd desktop
npm install
npm run build
```

### Q7: 如何备份数据

```bash
# 备份数据库
cp agent_notify/state/events.db ~/backup/

# 或通过 Web UI 导出
# http://localhost:18865 -> 数据管理 -> 导出 JSON
```

---

## 进阶配置

### 自定义端口

```bash
# Linux/Mac
export AGENT_NOTIFY_PORT=28865
python3 -m agent_notify.server

# 或直接指定
python3 -m agent_notify.server 28865
```

### 配置 HTTPS

```python
# 修改 server.py
from http.server import HTTPServer
import ssl

server = HTTPServer(('localhost', 18865), Handler)
server.socket = ssl.wrap_socket(server.socket,
                                certfile='cert.pem',
                                keyfile='key.pem',
                                server_side=True)
server.serve_forever()
```

### 多实例部署

```bash
# 不同端口运行多个实例
python3 -m agent_notify.server 18865 --db /path/to/db1.db
python3 -m agent_notify.server 18866 --db /path/to/db2.db
```

---

## 技术支持

### 项目地址

- **GitHub**: https://github.com/chenxilin1994/agent-notify
- **Issues**: https://github.com/chenxilin1994/agent-notify/issues

### 文档

- **README**: `/agent-notify/README.md`
- **桌面应用**: `/agent-notify/desktop/README.md`
- **API文档**: http://localhost:18865/api/docs

### 社区

- 提交 Issue 反馈问题
- Pull Request 贡献代码
- Star 项目表示支持 ⭐

---

## 许可证

MIT License - 可自由使用、修改、分发。

---

**安装愉快！享受 Claude Code 的通知体验 🎉**