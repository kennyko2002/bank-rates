# Bank Rates - Vercel 部署指南

## 🚀 快速部署 (3 步驟)

### 1. 推送到 GitHub
```bash
cd C:\Users\kenny\bank-rates-deploy
git init
git add .
git commit -m "Initial deploy"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/bank-rates.git
git push -u origin main
```

### 2. Vercel 連動 GitHub
1. 進入 [Vercel Dashboard](https://vercel.com/dashboard)
2. 點擊 **Add New...** → **Project**
3. Import 你的 GitHub repo
4. Framework Preset: **Other** (自動偵測)
5. 點擊 **Deploy**

### 3. 設定環境變數 (重要!)
在 Vercel 專案設定中：
- Settings → **Environment Variables**
- 新增：
  - Name: `MONGODB_URI`
  - Value: `mongodb+srv://api_readonly:YOUR_PASSWORD@cluster0.6abxj.mongodb.net/cbc_rate?retryWrites=true&w=majority`
  - Environment: **Production**, **Preview**, **Development** 全勾選
- 儲存後 **重新部署** (Redeploy)

---

## 🔐 MongoDB Atlas 設定 (必做)

### 建立唯讀帳號
1. 進入 [Atlas Dashboard](https://cloud.mongodb.com)
2. 左側 **Database Access** → **Add New Database User**
3. 設定：
   - Username: `api_readonly`
   - Password: 自動產生或自訂強密碼
   - **Database User Privileges** → **Add Custom Role**
     - Role Name: `readOnlyCbcRate`
     - Privileges:
       - Database: `cbc_rate`
       - Collections: `rate_data`, `rate_changes`
       - Actions: `find` (唯讀)
   - 指派此角色給該使用者

### 更新連線字串
把新帳號密碼填入 Vercel 的 `MONGODB_URI`：
```
mongodb+srv://api_readonly:YOUR_PASSWORD@cluster0.6abxj.mongodb.net/cbc_rate?retryWrites=true&w=majority
```

---

## 📁 專案結構

```
bank-rates-deploy/
├── vercel.json          # Vercel 設定
├── requirements.txt     # Python 依賴
├── index.html           # 前端頁面 (靜態)
└── api/
    └── rates.py         # FastAPI 後端 (Serverless Function)
```

---

## 🌐 部署後網址

| 類型 | 格式 |
|------|------|
| 前端頁面 | `https://your-project.vercel.app` |
| API 健康檢查 | `https://your-project.vercel.app/api/health` |
| 利率查詢 | `https://your-project.vercel.app/api/rates` |
| 統計摘要 | `https://your-project.vercel.app/api/rates/stats` |
| 異動記錄 | `https://your-project.vercel.app/api/changes` |
| 最新更新 | `https://your-project.vercel.app/api/latest-update` |
| 銀行列表 | `https://your-project.vercel.app/api/banks` |

---

## 🛠️ 本地測試

```bash
# 安裝依賴
pip install -r requirements.txt

# 設定環境變數
# Windows PowerShell
$env:MONGODB_URI="mongodb+srv://api_readonly:PASSWORD@cluster0.6abxj.mongodb.net/cbc_rate?retryWrites=true&w=majority"

# 啟動本地測試
python api/rates.py
# 訪問 http://localhost:8765
```

---

## 🔧 常見問題

### Q: 部署失敗怎麼辦？
查看 Vercel 的 **Function Logs**，常見原因：
- `MONGODB_URI` 未設定或格式錯誤
- Python 版本不符 (Vercel 預設 3.9，可在 `vercel.json` 指定)
- 依賴安裝失敗 (檢查 `requirements.txt`)

### Q: API 回應慢 / Timeout?
- Vercel Serverless Function 預設 10 秒，可在 `vercel.json` 加 `"maxDuration": 30`
- 確認 MongoDB Atlas IP 白名單允許所有 (0.0.0.0/0) 或 Vercel IP 範圍

### Q: CORS 錯誤?
`rates.py` 已內建 `CORSMiddleware(allow_origins=["*"])`，正常不會有問題。

### Q: 要自訂網域?
Vercel Dashboard → Settings → Domains → Add
- 加入 `rates.yourdomain.com`
- 在 DNS 設定 CNAME 指向 `cname.vercel-dns.com`

---

## 📝 更新部署

```bash
git add .
git commit -m "Update something"
git push origin main
# Vercel 自動偵測並重新部署
```

---

## 💰 成本

| 項目 | 免費額度 | 超過後 |
|------|----------|--------|
| Vercel Bandwidth | 100 GB/月 | $20/月 (Pro) |
| Vercel Function | 100 GB-hours/月 | 包含在 Pro |
| MongoDB Atlas M0 | 512 MB 永久免費 | $9/月 (M10) |

**小規模查詢服務完全在免費額度內！**