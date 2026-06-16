# 自动打开窗口功能说明

## 功能概述

当 Claude Code 或 Codex 完成回复后，Windows 桌面应用会：
1. **自动检测新事件**
2. **打开已启动的窗口**（不创建新窗口）
3. **刷新页面显示最新数据**

---

## 工作原理

### 双重检测机制

为了确保可靠性，使用了两种检测方式：

#### 方式1: Flag 文件监听（即时响应）⚡

```
Hook 完成 → notify.py 写入 flag 文件 → Electron 监听文件变化 → 立即打开窗口
```

**特点**：
- **响应速度**: < 1秒（几乎是即时）
- **实现方式**: Node.js `fs.watch()` 监听文件系统
- **文件路径**: `state/new_event.flag`

**工作流程**:
1. Claude/Codex 完成任务
2. notify.py 调用 `insert_event()` 记录到 SQLite
3. notify.py 写入 `state/new_event.flag`（包含时间戳）
4. Electron 文件监听器检测到文件创建
5. Electron 立即打开窗口并刷新
6. Electron 删除 flag 文件（避免重复触发）

#### 方式2: API 轮询（备用机制）🔄

```
Hook 完成 → SQLite total_events 增加 → Electron 每5秒检查 → 打开窗口
```

**特点**：
- **响应速度**: 最多 5秒延迟
- **实现方式**: HTTP 请求 `/api/stats`
- **触发条件**: `total_events` 数值增加

**工作流程**:
1. Electron 每5秒请求 `http://localhost:18865/api/stats`
2. 比较 `total_events` 是否大于上次记录的值
3. 如果增加，打开窗口并刷新
4. 更新 `lastEventCount` 防止重复触发

---

## 为什么使用双重机制？

### Flag 文件监听的优点
- ✅ **即时响应**: 几乎零延迟
- ✅ **系统原生**: Node.js 文件监听性能好
- ❌ **依赖**: 需要文件系统权限

### API 轮询的优点
- ✅ **稳定性**: 不依赖文件系统
- ✅ **跨平台**: 所有平台都能工作
- ❌ **延迟**: 最多5秒等待

**组合使用** = 最佳体验 + 高可靠性

---

## 配置说明

### 服务器端口检查

Electron 应用启动时：
```javascript
// 检查18865端口是否已有服务器
const isRunning = await checkServerRunning();
if (isRunning) {
  console.log('Server already running - skipping startup');
} else {
  startServer(); // 启动新服务器
}
```

**防止冲突**：
- ✅ 检测现有服务器，避免端口冲突
- ✅ 连接现有服务器，共享同一数据库
- ✅ 单一数据库，不会重复记录

---

## 使用指南

### 用户操作

1. **启动应用**
   - 双击桌面图标或便携版 exe
   - 应用自动检查服务器并连接

2. **正常使用**
   - 使用 Claude Code 或 Codex
   - 任务完成后，窗口自动打开并刷新

3. **关闭窗口**
   - 点击关闭按钮 (X)
   - 窗口隐藏到托盘（不退出）

4. **再次触发**
   - Hook 完成后，窗口自动显示
   - 页面自动刷新显示最新数据

5. **托盘控制**
   - 双击托盘图标：打开窗口
   - 右键菜单：
     - 打开界面
     - 刷新数据
     - 重启服务
     - 退出

---

## 避免重复记录

### 问题：会不会记录两次？

**不会！原因如下**：

| 场景 | 结果 |
|------|------|
| Hook 触发一次 | ✅ 记录一次 |
| Electron 连接现有服务器 | ✅ 共享数据库 |
| 多个 Electron 实例 | ❌ 不支持（单实例模式） |

### 数据流程

```
Claude Code Hook 触发
  ↓
notify.py 处理
  ↓
insert_event() → SQLite (单次写入)
  ↓
写入 flag 文件 (通知 Electron)
  ↓
Electron 检测 → 打开窗口 → 刷新显示
```

**关键点**：
- Hook 只触发一次
- notify.py 只调用一次 `insert_event()`
- SQLite 是单一数据源
- Electron 只是读取和显示

---

## 技术细节

### Flag 文件内容

文件内容：ISO 8601 时间戳
```
2026-06-16T17:45:30.123456+00:00
```

用途：
- 确认文件写入时间
- 可用于调试和日志

### 文件监听代码

```javascript
// 监听 state 目录
flagFileWatcher = fs.watch(stateDir, (eventType, filename) => {
  if (filename === 'new_event.flag' && eventType === 'rename') {
    // 文件创建或重命名
    setTimeout(() => {
      if (fs.existsSync(FLAG_FILE)) {
        showAndRefreshWindow();
        fs.unlinkSync(FLAG_FILE); // 删除标记
      }
    }, 100);
  }
});
```

### 轮询代码

```javascript
// 每5秒检查
setInterval(async () => {
  const stats = await fetchStats();
  if (stats.total_events > lastEventCount) {
    lastEventCount = stats.total_events;
    showAndRefreshWindow();
  }
}, 5000);
```

---

## 性能优化

### Flag 文件方式
- CPU: 极低（文件监听是异步的）
- 内存: < 1MB
- 响应: < 1秒

### API 轮询方式
- CPU: 低（每5秒一次 HTTP 请求）
- 内存: < 1MB
- 响应: 最多5秒

### 组合性能
- 总体: 极佳（两种方式互补）
- 用户体验: 即时 + 稳定

---

## 故障排除

### 问题1: 窗口不自动打开

**可能原因**:
1. Flag 文件监听失败
2. API 轮询失败
3. Electron 未运行

**解决方法**:
```powershell
# 检查 Electron 是否运行
# 任务管理器 → Agent Notify.exe

# 检查服务器
curl http://localhost:18865/api/stats

# 检查 flag 文件
dir state\new_event.flag

# 手动触发
# 托盘右键 → 打开界面
```

### 问题2: 重复打开窗口

**原因**: Flag 文件未被删除

**解决**:
```powershell
# 手动删除 flag 文件
del state\new_event.flag

# 重启应用
# 托盘右键 → 退出
# 重新启动应用
```

### 问题3: 端口冲突

**症状**: 启动时提示端口占用

**解决**:
```powershell
# 关闭其他服务器
netstat -ano | findstr :18865
taskkill /PID <PID> /F

# 重启应用
```

---

## 未来改进

可能的增强功能：

1. **WebSocket 实时推送** (更实时)
   - Python 服务器推送事件
   - Electron 接收 WebSocket 消息
   - 响应速度: 毫秒级

2. **声音提示** (听觉反馈)
   - 新事件到达时播放提示音
   - 可自定义声音文件

3. **桌面通知** (系统通知)
   - Windows Toast 通知
   - 显示摘要内容

4. **自动聚焦** (窗口激活)
   - 强制窗口到前台
   - 解决最小化状态

---

## 总结

这个功能实现了：
- ✅ **即时响应**: < 1秒打开窗口
- ✅ **高可靠性**: 双重检测机制
- ✅ **无冲突**: 单一数据源
- ✅ **用户友好**: 自动化操作

**体验**: 任务完成 → 窗口自动弹出 → 查看结果 🎉