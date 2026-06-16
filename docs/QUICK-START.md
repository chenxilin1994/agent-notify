# Agent Notify - 快速开始

**3 分钟快速安装指南**

---

## 🚀 最快安装方式

### Web UI 版本（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/chenxilin1994/agent-notify.git

# 2. 启动服务器
cd agent-notify
python3 -m agent_notify.server

# 3. 打开浏览器
# http://localhost:18865
```

✅ **完成！** 现在配置 Hook（见下方）

---

## 📦 Windows 桌面应用

```powershell
# 1. 克隆项目
git clone https://github.com/chenxilin1994/agent-notify.git
cd agent-notify\desktop

# 2. 安装依赖
npm install

# 3. 构建应用
npm run build

# 4. 安装
# dist\Agent Notify Setup 1.0.0.exe
```

---

## ⚙️ 配置 Hook（必需）

编辑 `~/.claude/settings.json`：

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

**Windows 用户**: 将 `python3` 改为 `python`

---

## ✅ 验证安装

```bash
# 运行 Claude Code
claude

# 执行任务
> "写一个 Hello World 程序"

# 任务完成后，Web UI 应自动打开
```

---

## 📖 完整教程

查看完整安装指南：
- [详细教程](docs/INSTALLATION-GUIDE.md)
- [常见问题](docs/FAQ.md)

---

## 🆘 需要帮助？

- GitHub Issues: https://github.com/chenxilin1994/agent-notify/issues
- 检查服务器: http://localhost:18865/api/stats

---

**就这么简单！开始使用吧 🎉**