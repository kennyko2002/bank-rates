"""
Vercel Serverless Function - Bank Rates API
適配 Vercel @vercel/python + Mangum
"""

import os
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from datetime import datetime, timezone
from typing import Optional
from mangum import Mangum


# ========== 設定 ==========
MONGO_URI = os.environ.get("MONGODB_URI")
if not MONGO_URI:
    raise ValueError("MONGODB_URI environment variable is required")

DB_NAME = "cbc_rate"
RATE_COLLECTION = "rate_data"
CHANGES_COLLECTION = "rate_changes"
# ===========================


# MongoDB 連線
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)
db = client[DB_NAME]
rate_coll = db[RATE_COLLECTION]
changes_coll = db[CHANGES_COLLECTION]


app = FastAPI(title="Bank Rates API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    try:
        client.admin.command("ping")
        return {"status": "ok", "mongodb": "connected"}
    except Exception as e:
        return {"status": "error", "mongodb": str(e)}


@app.get("/api/rates")
async def get_rates(
    bank: Optional[str] = Query(None, description="銀行名稱關鍵字"),
    term_month: Optional[int] = Query(None, description="存款月數 1-12"),
    amount: Optional[str] = Query(None, description="額度關鍵字"),
    item_type: Optional[str] = Query(None, description="利率項目"),
    limit: int = Query(500, ge=1, le=2000, description="回傳筆數上限"),
    sort: str = Query("-fixed_rate_pct", description="排序欄位"),
):
    """查詢牌告利率資料"""
    query = {}

    if bank:
        query["bank_name"] = {"$regex": bank, "$options": "i"}

    if term_month:
        term_map = {
            1: "１月", 2: "２月", 3: "３月", 4: "４月",
            5: "５月", 6: "６月", 7: "７月", 8: "８月",
            9: "９月", 10: "１０月", 11: "１１月", 12: "１２月"
        }
        if term_month in term_map:
            query["term_chinese"] = term_map[term_month]

    if amount:
        query["quota_chinese"] = {"$regex": amount, "$options": "i"}

    if item_type:
        query["rate_item_name"] = item_type

    sort_field = sort.lstrip("-")
    sort_dir = -1 if sort.startswith("-") else 1

    valid_sort_fields = ["fixed_rate_pct", "floating_rate_pct", "data_date", "bank_name", "effective_date"]
    if sort_field not in valid_sort_fields:
        sort_field = "fixed_rate_pct"
        sort_dir = -1

    cursor = rate_coll.find(query, {"_id": 0}).sort(sort_field, sort_dir).limit(limit)
    results = list(cursor)

    total = rate_coll.count_documents(query)

    return {
        "data": results,
        "total": total,
        "returned": len(results),
        "query": {
            "bank": bank,
            "term_month": term_month,
            "amount": amount,
            "item_type": item_type,
            "limit": limit,
            "sort": sort
        }
    }


@app.get("/api/rates/stats")
async def get_rates_stats():
    """取得統計摘要"""
    total = rate_coll.count_documents({})
    banks = rate_coll.distinct("bank_name")
    item_types = rate_coll.distinct("rate_item_name")
    terms = rate_coll.distinct("term_chinese")

    pipeline = [
        {"$match": {"fixed_rate_pct": {"$ne": None}}},
        {"$group": {
            "_id": None,
            "max_rate": {"$max": "$fixed_rate_pct"},
            "min_rate": {"$min": "$fixed_rate_pct"},
            "avg_rate": {"$avg": "$fixed_rate_pct"}
        }}
    ]
    agg_result = list(rate_coll.aggregate(pipeline))
    stats = agg_result[0] if agg_result else {}

    return {
        "total_records": total,
        "bank_count": len(banks),
        "banks": sorted(banks),
        "item_types": item_types,
        "terms": sorted([t for t in terms if t]),
        "max_fixed_rate": round(stats.get("max_rate", 0), 3),
        "min_fixed_rate": round(stats.get("min_rate", 0), 3),
        "avg_fixed_rate": round(stats.get("avg_rate", 0), 3),
    }


@app.get("/api/changes")
async def get_changes(
    bank: Optional[str] = Query(None, description="銀行名稱關鍵字"),
    term: Optional[str] = Query(None, description="存期關鍵字"),
    change_type: Optional[str] = Query(None, description="異動別"),
    effective_date_from: Optional[str] = Query(None, description="生效日期起"),
    effective_date_to: Optional[str] = Query(None, description="生效日期迄"),
    limit: int = Query(500, ge=1, le=2000),
    sort: str = Query("-data_date", description="排序欄位"),
):
    """查詢利率異動記錄"""
    query = {}

    if bank:
        query["bank_name"] = {"$regex": bank, "$options": "i"}

    if term:
        query["term"] = {"$regex": term, "$options": "i"}

    if change_type:
        query["change_type"] = change_type

    if effective_date_from or effective_date_to:
        query["effective_date"] = {}
        if effective_date_from:
            query["effective_date"]["$gte"] = effective_date_from
        if effective_date_to:
            query["effective_date"]["$lte"] = effective_date_to

    sort_field = sort.lstrip("-")
    sort_dir = -1 if sort.startswith("-") else 1

    cursor = changes_coll.find(query, {"_id": 0}).sort(sort_field, sort_dir).limit(limit)
    results = list(cursor)

    total = changes_coll.count_documents(query)

    return {
        "data": results,
        "total": total,
        "returned": len(results)
    }


@app.get("/api/latest-update")
async def get_latest_update():
    """取得最新資料更新時間"""
    latest_rate = rate_coll.find_one(
        {},
        {"data_date": 1, "effective_date": 1, "_id": 0},
        sort=[("data_date", -1)]
    )

    latest_change = changes_coll.find_one(
        {},
        {"data_date": 1, "effective_date": 1, "_id": 0},
        sort=[("data_date", -1)]
    )

    return {
        "rate_data": latest_rate,
        "rate_changes": latest_change,
        "checked_at": datetime.now(timezone.utc).isoformat()
    }


@app.get("/api/banks")
async def get_banks():
    """取得所有銀行列表"""
    banks = rate_coll.distinct("bank_name")
    return {"banks": sorted(banks)}


# Vercel 需要這個 handler
handler = Mangum(app)


# 本地測試用
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8765)