# Icon Creation Guide

Agent Notify 应用需要一个图标文件 `icon.ico`

## 创建方法

### 方法 1: 使用在线工具

1. 准备一个 PNG 图片 (推荐 256x256 或 512x512)
2. 访问: https://www.icoconverter.com/
3. 上传 PNG
4. 选择 ICO 格式
5. 下载生成的 `icon.ico`
6. 放到 desktop 目录

### 方法 2: 使用 ImageMagick (本地)

```bash
# 安装 ImageMagick
sudo apt install imagemagick  # Linux
# 或 Windows: https://imagemagick.org/

# 转换 PNG 到 ICO
convert icon.png -resize 256x256 icon.ico
```

### 方法 3: 使用 Python (本地)

```bash
# 安装 Pillow
pip install Pillow

# 转换
python create_icon.py icon.png icon.ico
```

## 推荐图标设计

- 🎨 颜色: 绿色/青色主题 (与应用主题匹配)
- 📐 尺寸: 256x256 或 512x512
- 🔔 主题: 通知铃铛、消息图标、或字母 "A"

## 当前状态

如果没有 icon.ico, Electron 会使用默认图标。
构建脚本会提示这个情况但不会阻止构建。

## 快速测试

如果想快速测试, 可以使用默认图标:
```bash
npm start  # 会使用默认 Electron 图标
```