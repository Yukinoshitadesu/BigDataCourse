# BigDataCourse
教育大數據課程

# Discord 公車模擬器 Bot 說明

這段程式碼建立了一個 Discord 機器人，提供以下功能：
1. 使用 Google Drive 上的路線數據，動態查詢公車資訊。
2. 從台北市交通局取得公車事件數據 (`GetBusEvent`) 和路線詳細資料 (`GetPathDetail`)。
3. 支援使用 `%公車` 或 `%路線` 關鍵字查詢特定路線的目前狀況。
4. 支援 `%chat` 指令，整合 OpenAI 的 Ollama 模型，提供 AI 聊天功能。

## 功能概述
### 1. **路線數據讀取**
- 利用 Google Drive 連結轉換為下載 URL。
- 加載三種數據：
  - **路線資訊**：包含路線名稱及詳細資訊。
  - **站點資料**：各站點的中文與英文名稱。
  - **站點 ID 資料**：進一步補充站點與路線的對應關係。

### 2. **公車事件處理**
- 自動從 API (`GetBusEvent`) 獲取目前公車事件數據，包含：
  - 車輛位置。
  - 距離目標站的剩餘站數。
  - 車輛方向（GoBack 值）。
- 篩選並輸出最接近目標站的公車資訊。

### 3. **AI 聊天功能**
- 在 `%chat` 指令下，從本地檔案讀取初始提示詞 (Prompt)。
- 使用 OpenAI 的 `ollama` 模組呼叫模型，生成回應並回覆使用者。

### 4. **Discord 訊息處理**
- 機器人登入時會在伺服器內廣播歡迎訊息，指導用戶使用功能。
- 偵測 `%公車` 或 `%路線` 關鍵字後，引導用戶輸入路線名稱，並提供相關資訊。

## 程式結構
### 主要函數
- **`get_google_drive_download_url`**: 將 Google Drive 共享連結轉換為下載連結。
- **`get_bus_event_data`**: 從遠端 API 獲取並解壓縮公車事件數據。
- **`read_prompt_from_file`**: 從本地檔案讀取 AI 聊天的初始 Prompt。

### Discord 事件
- **`on_ready`**: 機器人登入時的初始化操作。
- **`on_message`**: 處理用戶訊息，根據指令執行對應功能。

## 需求與依賴
- **Python 模組**：
  - `discord.py`: Discord 機器人開發工具。
  - `ollama`: 用於 AI 模型的聊天應用。
  - `requests`: HTTP 請求模組，用於調用 API。
  - `pandas`: 處理數據表格。
  - `gzip` 和 `io`: 處理壓縮數據。
- **數據來源**：
  - 公車路線、站點數據：來自 Google Drive。
  - 公車實時事件與路線詳細資料：來自台北市交通局 API。

## 使用方法
1. **安裝依賴套件**：
   ```bash
   pip install discord.py pandas requests
