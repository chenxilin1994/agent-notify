# 窗口强制前台显示改进

## 问题

**用户反馈**：窗口自动打开但没有在最前端显示

**原因**：Windows 系统有窗口管理限制，防止应用程序随意抢占焦点

---

## 解决方案

### 多层强制显示机制

使用了以下技术组合：

#### 1. 窗口状态恢复
```javascript
// 如果窗口最小化，先恢复
if (mainWindow.isMinimized()) {
  mainWindow.restore();
}
```

#### 2. 临时置顶
```javascript
// 临时设置为最高优先级置顶
mainWindow.setAlwaysOnTop(true, 'floating');
// 100ms后恢复
setTimeout(() => mainWindow.setAlwaysOnTop(false), 100);
```

**说明**：
- `'floating'` 模式：浮动窗口优先级
- 临时置顶可以绕过 Windows 的焦点管理限制
- 短时间后恢复，避免永久遮挡其他窗口

#### 3. 窗口焦点
```javascript
mainWindow.focus();
mainWindow.moveTop();
```

#### 4. 任务栏闪烁（可选）
```javascript
mainWindow.flashFrame(true); // 闪烁吸引注意力
setTimeout(() => mainWindow.flashFrame(false), 100);
```

#### 5. 延迟刷新
```javascript
// 先显示窗口，200ms后再刷新（避免失去焦点）
setTimeout(() => mainWindow.reload(), 200);
```

---

## 改进细节

### 创建窗口时添加属性

```javascript
new BrowserWindow({
  // ...
  focusable: true,      // 可聚焦
  skipTaskbar: false,   // 显示在任务栏
})
```

### 监听显示事件

```javascript
mainWindow.on('show', () => {
  mainWindow.focus(); // 每次显示时自动聚焦
});
```

### 托盘菜单增强

新增了 **"强制前台显示"** 选项：

```javascript
{
  label: '强制前台显示',
  click: () => {
    // 使用最高优先级置顶
    mainWindow.setAlwaysOnTop(true, 'screen-saver');
    mainWindow.focus();
    // 1秒后恢复
    setTimeout(() => mainWindow.setAlwaysOnTop(false), 1000);
  }
}
```

---

## 工作流程

### Hook完成后的完整流程

```
Hook完成
  ↓
notify.py写入flag文件
  ↓
Electron检测到flag文件（<1秒）
  ↓
调用showAndRefreshWindow()
  ↓
1. restore() - 恢复最小化状态
2. show() - 显示窗口
3. setAlwaysOnTop(true) - 强制置顶
4. focus() - 获取焦点
5. flashFrame() - 闪烁提示
6. moveTop() - 移到Z-order顶部
  ↓
等待200ms
  ↓
reload() - 刷新页面显示新数据
  ↓
等待100ms
  ↓
setAlwaysOnTop(false) - 恢复正常
flashFrame(false) - 停止闪烁
  ↓
窗口在最前端，显示最新数据 ✅
```

---

## Windows 窗口管理限制

### 为什么需要这些技巧？

**Windows 系统规则**：
- 防止恶意应用频繁抢占焦点
- 只有用户主动交互的应用才能获得焦点
- 后台应用强行激活窗口会被阻止

**Electron/Chrome 的限制**：
- 遵循 Windows 的窗口管理规则
- 需要特殊技巧绕过限制

### 技术对比

| 方法 | 效果 | 问题 |
|------|------|------|
| `focus()` | 一般 | 可能被系统阻止 |
| `show()` | 显示窗口 | 不保证焦点 |
| `setAlwaysOnTop(true)` | **强力** | 可能遮挡其他窗口 |
| `flashFrame()` | 提示用户 | 需手动点击 |

**最佳组合**：临时置顶 + focus + flashFrame

---

## 使用指南

### 自动显示（推荐）

Hook完成后自动触发，无需用户操作。

### 手动显示

**方式1：托盘双击**
- 双击托盘图标
- 窗口自动前台显示

**方式2：托盘菜单**
- 右键托盘 → "打开界面"
- 窗口前台显示并刷新

**方式3：强制显示**
- 右键托盘 → "强制前台显示"
- 使用最高优先级置顶（screen-saver级别）
- 持续1秒确保窗口在最前端

---

## 性能影响

### CPU和内存

- **临时置顶**：几乎无影响（仅改变窗口属性）
- **flashFrame**：极低（闪烁任务栏图标）
- **延迟刷新**：200ms等待（用户无感知）

### 用户体验

- ✅ 窗口立即出现（<1秒）
- ✅ 自动获得焦点（用户可直接查看）
- ✅ 短暂闪烁提示（吸引注意力）
- ✅ 自动恢复正常（不永久遮挡）

---

## 测试验证

### 测试步骤

1. **启动应用**
   - 窗口正常显示
   - 托盘图标出现

2. **隐藏窗口**
   - 点击关闭按钮（X）
   - 窗口隐藏到托盘

3. **触发Hook**
   - 使用 Claude Code/Codex
   - 完成一个任务

4. **验证结果**
   - ✅ 窗口自动显示
   - ✅ 在最前端（遮挡其他窗口）
   - ✅ 任务栏闪烁（短暂）
   - ✅ 显示最新数据

---

## 已知限制

### Windows 10/11 专注助手

如果用户开启了"专注助手"，可能会：
- 阻止窗口闪烁
- 阻止通知弹窗

**解决**：手动关闭专注助手，或使用"强制前台显示"选项

### 远程桌面/虚拟机

在远程桌面环境中：
- 窗口管理可能不同
- 需要使用"强制前台显示"

---

## 未来改进

可能的增强：

### 1. 播放提示音
```javascript
// 新事件到达时播放声音
mainWindow.webContents.executeJavaScript(`
  new Audio('notification.mp3').play()
`);
```

### 2. Windows Toast 通知
```javascript
// 系统级通知（不受专注助手影响）
const { Notification } = require('electron');
new Notification({
  title: '新对话记录',
  body: '点击查看',
}).show();
```

### 3. 使用 user32.dll API
```javascript
// 直接调用 Windows API（最强力）
const user32 = require('user32');
user32.SetForegroundWindow(mainWindow.getNativeWindowHandle());
```

---

## 总结

**改进效果**：
- ✅ 窗口自动显示在最前端
- ✅ 用户无需手动点击任务栏
- ✅ 短暂闪烁提示新事件
- ✅ 自动恢复正常状态

**技术要点**：
- 临时置顶绕过 Windows 限制
- 多层调用确保窗口激活
- 延迟刷新避免失去焦点
- 托盘菜单提供备用方案

**用户体验**：从"窗口在后台显示" → "窗口自动前台弹出" 🎉