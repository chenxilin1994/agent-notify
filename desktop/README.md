# Agent Notify Desktop App

Windows 桌面应用版本

## 开发环境准备

1. 安装 Node.js: https://nodejs.org/
2. 安装 Python 3.x
3. 安装依赖:
```bash
cd desktop
npm install
```

## 开发运行

```bash
npm start
```

## 构建 Windows 应用

### 构建安装包版本:
```bash
npm run build
```

输出文件: `dist/Agent Notify Setup 1.0.0.exe`

### 构建便携版:
```bash
npm run build-portable
```

输出文件: `dist/AgentNotify-Portable.exe`

## 应用功能

- ✅ 系统托盘图标
- ✅ 双击托盘图标打开界面
- ✅ 右键菜单控制服务
- ✅ 关闭窗口时隐藏到托盘
- ✅ 后台 Python 服务自动启动
- ✅ 新端口 18865

## 安装图标

需要准备 `icon.ico` 文件放在 desktop 目录下。
可以使用在线工具转换 PNG 到 ICO:
https://www.icoconverter.com/

## 项目结构

```
desktop/
├── package.json      # Electron 配置
├── main.js           # 主进程
├── icon.ico          # 应用图标
└── dist/             # 构建输出
```

打包时会包含:
- agent_notify/  Python 后端
- web/           Web UI
- bin/           工具脚本