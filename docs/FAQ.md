# 常见问题 (FAQ)

Agent Notify 使用中的常见问题解答

---

## 安装问题

### Q1: Python 版本要求？

**需要**: Python 3.10 或更高版本

**检查**:
```bash
python3 --version  # Linux/Mac
python --version   # Windows
```

**安装**:
- Ubuntu/Debian: `sudo apt install python3`
- Mac: `brew install python3`
- Windows: https://www.python.org/downloads/

---

### Q2: 端口 18865 被占用？

**错误**: `OSError: [Errno 98] Address already in use`

**解决方式 1**: 查找并关闭占用进程
```bash
# Linux/Mac
lsof -i :18865
kill -9 <PID>

# Windows
netstat -ano | findstr :18865
taskkill /PID <PID> /F
```

**解决方式 2**: 使用其他端口
```bash
# 使用端口 28865
python3 -m agent_notify.server 28865

# 同时更新配置：
# desktop/main.js 中的 PORT 值
# 或 Web UI 的默认端口
```

---

### Q3: npm install 失败？

**错误**: 网络连接失败 / 下载超时

**解决**: 使用中国镜像源
```powershell
# 设置 npm 镜像
npm config set registry https://registry.npmmirror.com

# 设置 Electron 镜像
$env:ELECTRON_MIRROR="https://npmmirror.com/mirrors/electron/"

# 重新安装
npm install
```

---

### Q4: Electron 构建失败？

**错误**: `electron-builder` 找不到或下载失败

**解决步骤**:

1. **检查 Node.js 版本**
```powershell
node -v  # 需要 v18+
npm -v
```

2. **清理缓存重新安装**
```powershell
rm -rf node_modules package-lock.json
npm install
```

3. **手动下载 Electron**
```powershell
# 如果自动下载失败，手动下载
wget https://npmmirror.com/mirrors/electron/28.0.0/electron-v28.0.0-win32-x64.zip
# 解压到 node_modules/electron/dist/
```

---

## Hook 配置问题

### Q5: Hook 不触发？

**症状**: Claude Code 完成任务后，Web UI 不自动打开

**检查清单**:

1. **配置文件是否存在？**
```bash
ls ~/.claude/settings.json  # Linux/Mac
ls $env:USERPROFILE\.claude\settings.json  # Windows
```

2. **JSON 格式是否正确？**
```bash
# 使用 JSON 验证工具
python3 -c "import json; json.load(open('~/.claude/settings.json'))"
```

3. **Python 命令是否正确？**
```bash
# Linux/Mac 使用 python3
which python3

# Windows 使用 python
where python
```

4. **模块是否可导入？**
```bash
python3 -m agent_notify.notify --help
```

**手动测试 Hook**:
```bash
# 模拟 Claude Code 调用
python3 -m agent_notify.notify

# 检查输出是否有错误
```

---

### Q6: Hook 路径问题？

**错误**: `ModuleNotFoundError: No module named 'agent_notify'`

**原因**: Claude Code 无法找到项目目录

**解决**: 添加 `--project-dir` 参数

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
          "/完整路径/agent-notify"
        ]
      }
    ]
  }
}
```

**完整路径示例**:
- Linux: `/home/username/.local/share/agent-notify`
- Mac: `/Users/username/.local/share/agent-notify`
- Windows: `C:\\Users\\username\\agent-notify`

---

## 运行问题

### Q7: 数据库锁定？

**错误**: `sqlite3.OperationalError: database is locked`

**原因**: 多个进程同时访问数据库

**解决方式 1**: 关闭其他实例
```bash
# 查找所有 Python 进程
ps aux | grep agent_notify

# 关闭多余进程
kill <PID>
```

**解决方式 2**: 重启服务器
```bash
# 停止服务器
pkill -f agent_notify.server

# 重启
python3 -m agent_notify.server
```

---

### Q8: Web UI 加载慢？

**原因**: 数据量过大或网络问题

**解决方式 1**: 清理旧数据
```bash
# 通过 Web UI
# http://localhost:18865 -> 数据管理 -> 清理数据 -> 30天前
```

**解决方式 2**: 使用分页
```bash
# API 自动分页，每页 50 条
# 如果自定义，修改 server.py 中的 PAGE_SIZE
```

---

### Q9: 桌面应用窗口不显示？

**症状**: Electron 启动但无窗口

**检查**:

1. **服务器是否启动？**
```bash
curl http://localhost:18865/api/stats
```

2. **日志查看**
```powershell
# 右键托盘图标 -> 查看日志
# 或查看控制台输出
```

3. **防火墙设置**
```powershell
# 允许应用通过防火墙
# Windows 安全中心 -> 防火墙 -> 允许应用
```

---

## 数据问题

### Q10: 如何备份数据？

**方式 1**: 备份数据库文件
```bash
# 数据库位置
agent_notify/state/events.db

# 备份
cp agent_notify/state/events.db ~/backup/events-$(date +%Y%m%d).db
```

**方式 2**: 导出 JSON/CSV
```bash
# 通过 Web UI
# http://localhost:18865 -> 数据管理 -> 导出 JSON
```

**方式 3**: 自动备份脚本
```bash
# 每天备份
0 2 * * * cp ~/.local/share/agent-notify/state/events.db ~/backup/events-$(date +\%Y\%m\%d).db
```

---

### Q11: 如何迁移数据？

**迁移到新机器**:

1. **导出数据**
```bash
# 原机器
# Web UI -> 数据管理 -> 导出 JSON
```

2. **安装新实例**
```bash
# 新机器
git clone https://github.com/chenxilin1994/agent-notify.git
```

3. **导入数据**
```bash
# 将导出的 JSON 文件放到：
agent_notify/state/events.json

# 重启服务器会自动导入
```

---

### Q12: 数据丢失？

**预防措施**:

1. **定期备份** (见 Q10)

2. **检查数据库完整性**
```bash
sqlite3 agent_notify/state/events.db "PRAGMA integrity_check;"
```

3. **恢复损坏数据库**
```bash
# 如果损坏，从备份恢复
cp ~/backup/events-YYYYMMDD.db agent_notify/state/events.db
```

---

## 性能问题

### Q13: 如何优化性能？

**优化建议**:

1. **定期清理旧数据**
```bash
# 每月清理 90 天前的数据
0 0 1 * * python3 -c "from agent_notify.storage import Storage; Storage().cleanup(90)"
```

2. **限制每页数量**
```python
# server.py
PAGE_SIZE = 20  # 默认 50，可改为 20
```

3. **使用索引**
```sql
-- 数据库已有索引
-- 如果自定义查询慢，可添加：
CREATE INDEX idx_timestamp ON events(timestamp);
```

---

### Q14: 多用户共享？

**设置共享数据库**:

```bash
# 1. 创建共享目录
mkdir /shared/agent-notify

# 2. 修改数据库路径
export AGENT_NOTIFY_DB=/shared/agent-notify/events.db

# 3. 启动服务器
python3 -m agent_notify.server
```

**注意**: 需要处理并发访问（使用 WAL 模式）

---

## 更新问题

### Q15: 如何更新版本？

**Web UI 版本**:
```bash
cd agent-notify
git pull origin main

# 重启服务器
pkill -f agent_notify.server
python3 -m agent_notify.server
```

**桌面应用版本**:
```powershell
cd desktop
git pull origin main
npm install
npm run build
```

---

### Q16: 更新后数据兼容？

**检查**:
```bash
# 更新后，数据格式可能变化
# 查看 README.md 中的 CHANGELOG

# 如果数据不兼容：
# 1. 导出旧数据 (JSON)
# 2. 更新项目
# 3. 导入数据
```

---

## 开发问题

### Q17: 如何自定义主题？

**修改 CSS**:
```bash
# 编辑 web/styles.css
nano agent-notify/web/styles.css

# 主要颜色变量：
--accent-primary: #00ffa3;    # 主色调
--accent-secondary: #00c8ff;  # 辅助色
--background: #0a0e27;         # 背景
```

---

### Q18: 如何添加功能？

**开发步骤**:

1. **Fork 项目**
```bash
git clone https://github.com/你的用户名/agent-notify.git
```

2. **修改代码**
   - `agent_notify/server.py` - 后端 API
   - `web/app.js` - 前端逻辑
   - `web/index.html` - HTML 结构
   - `web/styles.css` - 样式

3. **测试**
```bash
python3 -m agent_notify.server
# http://localhost:18865 测试
```

4. **提交 Pull Request**
```bash
git add -A
git commit -m "添加新功能"
git push origin main
# GitHub -> Pull Request
```

---

## 其他问题

### Q19: 支持哪些系统？

| 系统 | Web UI | 桌面应用 |
|------|--------|----------|
| Windows | ✅ | ✅ |
| macOS | ✅ | ❌ (可自行构建) |
| Linux | ✅ | ❌ (可自行构建) |
| WSL | ✅ | ❌ |

---

### Q20: 如何报告问题？

**GitHub Issues**:
https://github.com/chenxilin1994/agent-notify/issues

**报告模板**:
```
### 问题描述
简要描述问题

### 系统信息
- 操作系统: Ubuntu 22.04 / Windows 11 / macOS 13
- Python版本: 3.12
- Node.js版本: 20.10 (桌面应用)

### 重现步骤
1. ...
2. ...
3. ...

### 期望结果
应该发生什么

### 实际结果
实际发生了什么

### 日志/截图
贴上错误日志或截图
```

---

### Q21: 如何贡献代码？

**贡献流程**:

1. Fork 项目
2. 创建分支 `git checkout -b feature/新功能`
3. 编写代码 + 测试
4. 提交 `git commit -m "添加新功能"`
5. Push `git push origin feature/新功能`
6. 创建 Pull Request
7. 等待审核合并

**代码规范**:
- Python: PEP 8
- JavaScript: ESLint
- 提交信息: 清晰简洁

---

## 📚 更多资源

- [完整教程](INSTALLATION-GUIDE.md)
- [快速开始](QUICK-START.md)
- [API文档](http://localhost:18865/api/docs)
- [GitHub](https://github.com/chenxilin1994/agent-notify)

---

**还有问题？提交 Issue 🙏**