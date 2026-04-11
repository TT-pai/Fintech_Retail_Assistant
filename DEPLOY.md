# 智汇投研Pro 部署指南

## 部署到 Streamlit Cloud（推荐）

### 前置条件

1. GitHub 账号
2. Streamlit Cloud 账号（免费，使用 GitHub 登录）
3. LLM API 密钥（iFlow / DeepSeek / 智谱AI 等任选其一）

---

### 步骤一：推送代码到 GitHub

```bash
# 初始化 Git 仓库（如果尚未初始化）
git init

# 添加远程仓库
git remote add origin https://github.com/你的用户名/你的仓库名.git

# 添加并提交所有文件
git add .
git commit -m "Initial commit: 智汇投研Pro"

# 推送到 GitHub
git push -u origin main
```

### 步骤二：注册 Streamlit Cloud

1. 访问 [share.streamlit.io](https://share.streamlit.io)
2. 使用 GitHub 账号登录

### 步骤三：部署应用

1. 点击 **"New app"**
2. 选择你的 GitHub 仓库
3. 设置入口文件为 `ui/app.py`
4. 点击 **"Deploy!"**

### 步骤四：配置 Secrets（重要！）

在 Streamlit Cloud 应用页面：

1. 点击右上角 **Settings** → **Secrets**
2. 添加以下配置：

```toml
# iFlow 心流模型配置（推荐）
OPENAI_API_KEY = "your_iflow_api_key_here"
OPENAI_BASE_URL = "https://apis.iflow.cn/v1"

# 应用配置
provider = "openai"
deep_think_model = "qwen3-max"
quick_think_model = "deepseek-v3.2"
EMBEDDING_MODEL = "shibing624/text2vec-base-chinese"
VECTOR_STORE_PATH = "./data/chroma"
KNOWLEDGE_GRAPH_PATH = "./data/knowledge_graph"
LOG_LEVEL = "INFO"
ENABLE_MEMORY = "true"
MAX_DEBATE_ROUNDS = "2"
```

> ⚠️ **安全提示**：请勿将 API 密钥提交到 GitHub！

### 步骤五：获取链接

部署成功后，你将获得一个类似以下的链接：

```
https://你的应用名-随机ID.streamlit.app
```

---

## 备选方案：Hugging Face Spaces

### 步骤一：创建 Space

1. 访问 [huggingface.co/new-space](https://huggingface.co/new-space)
2. 选择 **Streamlit** 作为 SDK
3. 命名你的 Space

### 步骤二：配置

创建 `.env` 文件（或在 Settings → Repository secrets 中配置）：

```bash
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://apis.iflow.cn/v1
provider=openai
deep_think_model=qwen3-max
quick_think_model=deepseek-v3.2
```

### 步骤三：推送代码

```bash
git remote add space https://huggingface.co/spaces/你的用户名/你的space名
git push space main
```

---

## 常见问题

### Q: 部署后应用显示 "Please wait..." 卡住？

A: 检查以下几点：
1. Secrets 是否正确配置
2. API 密钥是否有效
3. 查看 Streamlit Cloud 日志（Settings → Logs）

### Q: 如何更新应用？

A: 只需推送新代码到 GitHub，Streamlit Cloud 会自动重新部署：

```bash
git add .
git commit -m "Update: 描述你的更改"
git push
```

### Q: 如何查看日志？

A: 在 Streamlit Cloud 应用页面，点击右下角 **☰** → **Logs**

### Q: 免费额度限制？

A: Streamlit Cloud 免费版：
- 每月 1000 小时计算时间
- 1GB 内存
- 公开仓库无限制

---

## 部署检查清单

- [ ] 代码已推送到 GitHub
- [ ] 在 Streamlit Cloud 创建了应用
- [ ] 入口文件设置为 `ui/app.py`
- [ ] Secrets 已正确配置
- [ ] 应用可以正常访问
- [ ] 分享链接给用户