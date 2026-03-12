# imageManager（Windows 聊天图片管理工具）

一个面向微信/QQ/钉钉等 IM 图片目录的本地工具：

- 🔎 快速找到表情包、截图、GIF
- 🧠 支持语义检索（物体/动作/场景）
- 🔤 支持图片文字 OCR 检索
- 📊 自动统计常用图、重复图、长期未用图

> 目标：**真正可直接使用**，并且在 Windows 上开箱即用。

---

## 功能亮点

- **增量索引**：只处理新增或变更文件
- **多模态检索**：CLIP 语义 + OCR 文本 + 关键词混排
- **降级可用**：即使语义模型不可用，也可走关键词/OCR 搜索
- **偏好学习**：点击“我用了这张”后，自动累计热度，影响后续排序
- **整理分析**：最常用、重复图片（phash）、长期未使用

---

## 快速开始（Windows）

### 1) 安装

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2) 启动（推荐）

```bash
python run_app.py
```

或双击：

```bash
run_app.bat
```

### 3) 使用

1. 在左侧填写图片根目录（例如 IM 缓存目录）
2. 点击“扫描并更新”建立索引
3. 输入自然语言搜索，如：
   - `猫咪笑哭`
   - `会议截图里有 OK`
   - `谢谢老板 红包`
   - `跳舞庆祝`

---

## 技术方案（当前版本）

- **CLIP (`clip-ViT-B-32`)**：文本-图片语义对齐
- **BLIP Caption**：补充图片内容描述
- **EasyOCR（中英）**：识别截图/表情中的文字
- **SQLite**：本地隐私友好存储

排序分数采用：

`语义相似度 + 关键词命中 + 使用热度`

---

## 目录结构

- `image_manager/app.py`：Streamlit UI
- `image_manager/indexer.py`：目录扫描与索引流水线
- `image_manager/search.py`：检索与使用行为记录
- `image_manager/analytics.py`：偏好/重复/冷门分析
- `image_manager/config.py`：配置持久化
- `run_app.py` / `run_app.bat`：一键启动

---

## 后续可继续增强

- 向量库（FAISS/Qdrant）支持十万级图片
- Win11 托盘 + 全局快捷键呼出
- GIF 关键帧和动作检索增强
- 一键识别并整理低价值重复图
