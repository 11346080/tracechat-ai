# 全跡AI對話室 (TraceChat AI)

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.12-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)
![React](https://img.shields.io/badge/React-18-blue.svg)
![Redis](https://img.shields.io/badge/Redis-Stack-red.svg)

基於 **Redis Stack + FastAPI + Azure OpenAI** 的智能對話系統，支援多會話管理、訊息版本控制、全文搜尋和實時分析。

##  主要功能

-  **多會話管理**：支援多個獨立對話主題
-  **AI 智能回覆**：整合 Azure OpenAI GPT-4
-  **全文搜尋**：使用 RediSearch 快速檢索
-  **訊息恢復**：完整的軟刪除和復原機制
-  **活躍度分析**：小時粒度的對話趨勢統計
-  **實時通訊**：WebSocket 即時訊息推送

##  技術棧

### 後端
- **FastAPI** - 高效能 Web 框架
- **Redis Stack** - 內存數據庫（含 RediSearch）
- **Azure OpenAI** - GPT-4o 模型
- **Python 3.12** - 程式語言

### 前端
- **React 18** - UI 框架
- **Next.js** - 全棧框架
- **TypeScript** - 類型系統
- **CSS Modules** - 樣式管理

##  前置需求

- Python 3.12+
- Node.js 18+
- Redis Stack 7.0+
- Azure OpenAI API Key

##  快速開始

### 1. Clone 專案
- git clone https://github.com/yourusername/trackchat-ai.git
- cd trackchat-ai


### 2. 後端設定
cd backend

建立虛擬環境
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate

安裝依賴
pip install -r requirements.txt

設定環境變數
cp .env.example .env

編輯 .env，填入你的 Azure OpenAI API Key
啟動後端
uvicorn app:app --reload

### 3. 前端設定
cd frontend

安裝依賴
npm install

或
yarn install

啟動開發服務器
npm run dev

或
yarn dev


### 4. 啟動 Redis Stack

**Docker 方式（推薦）**：
docker run -d
--name redis-stack
-p 6379:6379
-p 8001:8001
redis/redis-stack:latest


**或下載安裝**：
- Windows: https://redis.io/docs/install/install-stack/windows/
- macOS: `brew install redis-stack`
- Linux: https://redis.io/docs/install/install-stack/linux/

### 5. 訪問應用

- 前端：http://localhost:3000
- 後端 API 文檔：http://localhost:8000/docs
- Redis Insight：http://localhost:8001

##  環境變數說明

請參考 `backend/.env.example` 檔案，主要配置：

| 變數 | 說明 | 必填 |
|------|------|------|
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API 密鑰 | ✅ |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI 端點 URL | ✅ |
| `REDIS_HOST` | Redis 主機位址 | ✅ |
| `REDIS_PORT` | Redis 端口 | ✅ |
| `REDIS_PASSWORD` | Redis 密碼（如有） | ❌ |

### 如何取得 Azure OpenAI API Key？

1. 訪問 [Azure Portal](https://portal.azure.com/)
2. 創建 Azure OpenAI 資源
3. 在「金鑰和端點」頁面複製 API Key

##  專案結構

trackchat-ai/
├── backend/ # 後端程式
│ ├── app.py # 主應用程式
│ ├── config.py # 配置管理
│ ├── requirements.txt # Python 依賴
│ ├── .env.example # 環境變數範本
│ ├── models/ # 數據模型
│ ├── services/ # 業務邏輯
│ ├── routes/ # API 路由
│ ├── database/ # 數據庫連接
│ └── utils/ # 工具函數
├── frontend/ # 前端程式
│ ├── pages/ # 頁面
│ ├── components/ # 組件
│ ├── styles/ # 樣式
│ ├── types/ # TypeScript 類型
│ └── package.json # Node 依賴
├── docs/ # 文檔
├── .gitignore # Git 忽略規則
└── README.md # 本檔案

##  開發指南

### 後端開發

cd backend

運行開發服務器（自動重載）
uvicorn app:app --reload

運行測試
pytest

代碼格式化
black .
flake8 .



### 前端開發

cd frontend

開發模式
npm run dev

構建生產版本
npm run build

啟動生產服務器
npm start


##  Redis 資料結構

本專案充分利用 Redis 的多種數據結構：

| 資料結構 | Key Pattern | 用途 |
|---------|-------------|------|
| Set | `active_sessions` | 會話集合 |
| List | `chat_history:{session_id}` | 訊息序列 |
| List | `deleted_history:{session_id}` | 刪除紀錄 |
| Hash | `chat_msg:{pk}` | 訊息 ORM |
| Stream | `chat_stream` | 事件日誌 |
| Index | `chatmessage_idx` | 全文搜尋索引 |

##  核心功能展示

### 1. 訊息版本控制
- 軟刪除機制（保留 30 天）
- 按時間順序復原
- 完整的操作日誌

### 2. 全文搜尋
- RediSearch 毫秒級搜尋
- 支援中文分詞
- 聚合統計

### 3. 實時分析
- WebSocket 實時推送
- 活躍度趨勢圖表
- 小時粒度統計

##  貢獻指南

歡迎提交 Issue 和 Pull Request！

1. Fork 本倉庫
2. 創建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交變更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 開啟 Pull Request


##  常見問題

### Q: 沒有 Azure OpenAI，可以用 OpenAI API 嗎？
A: 可以！修改 `backend/services/ai_service.py`，將 `AzureOpenAI` 改為 `OpenAI` 即可。

### Q: Redis Stack 和普通 Redis 有什麼區別？
A: Redis Stack 包含 RediSearch、RedisJSON 等模組，提供全文搜尋功能。普通 Redis 無法使用搜尋功能。


