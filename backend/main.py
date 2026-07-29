"""
MoneyTrace India — backend
Wraps World Bank, UN Comtrade, and data.gov.in APIs into unified endpoints
for the dashboard frontend.
"""
import os
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

COMTRADE_KEY = os.getenv("COMTRADE_SUBSCRIPTION_KEY")
DATA_GOV_IN_KEY = os.getenv("DATA_GOV_IN_KEY")

app = FastAPI(title="MoneyTrace India API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this before any real deployment
    allow_methods=["*"],
    allow_headers=["*"],
)

WORLD_BANK_BASE = "https://api.worldbank.org/v2"
COMTRADE_BASE = "https://comtradeapi.un.org/data/v1/get"


@app.get("/")
def root():
    return {"status": "ok", "service": "MoneyTrace India API"}


# ---------------------------------------------------------------------------
# World Bank — macro indicators (no key required)
# ---------------------------------------------------------------------------
@app.get("/api/worldbank/{country}/{indicator}")
async def worldbank_indicator(
    country: str = "IN",
    indicator: str = "NY.GDP.MKTP.CD",
    start: int = 2000,
    end: int = 2025,
):
    """
    Common indicator codes:
      NY.GDP.MKTP.CD   - GDP (current US$)
      FP.CPI.TOTL.ZG   - Inflation, consumer prices (annual %)
      SL.UEM.TOTL.ZS   - Unemployment, total (% of labor force)
      NE.TRD.GNFS.ZS   - Trade (% of GDP)
      BX.KLT.DINV.CD.WD - Foreign direct investment, net inflows (BoP, current US$)
    """
    url = f"{WORLD_BANK_BASE}/country/{country}/indicator/{indicator}"
    params = {"format": "json", "date": f"{start}:{end}", "per_page": 500}

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url, params=params)

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="World Bank API error")

    data = resp.json()
    if len(data) < 2 or data[1] is None:
        raise HTTPException(status_code=404, detail="No data found for this indicator/country")

    series = [
        {"year": row["date"], "value": row["value"]}
        for row in data[1]
        if row["value"] is not None
    ]
    series.sort(key=lambda r: r["year"])
    return {"country": country, "indicator": indicator, "series": series}


# ---------------------------------------------------------------------------
# UN Comtrade — trade flows (needs free subscription key)
# ---------------------------------------------------------------------------
@app.get("/api/comtrade/trade")
async def comtrade_trade(
    reporter: str = Query("699", description="Reporter country code, 699 = India"),
    partner: str = Query("0", description="Partner country code, 0 = World"),
    period: str = Query("2022", description="Year, e.g. 2022"),
    flow: str = Query("M", description="M = imports, X = exports"),
    cmd_code: str = Query("TOTAL", description="Commodity code, TOTAL = all commodities"),
):
    if not COMTRADE_KEY:
        raise HTTPException(
            status_code=503,
            detail=(
                "COMTRADE_SUBSCRIPTION_KEY not set. Register a free key at "
                "https://comtradeplus.un.org and add it to backend/.env"
            ),
        )

    url = f"{COMTRADE_BASE}/C/A/HS"
    params = {
        "reporterCode": reporter,
        "partnerCode": partner,
        "period": period,
        "flowCode": flow,
        "cmdCode": cmd_code,
        "subscription-key": COMTRADE_KEY,
    }

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.get(url, params=params)
    except httpx.ReadTimeout:
        raise HTTPException(
            status_code=504,
            detail="Comtrade API timed out. It can be slow at times — try again in a moment.",
        )
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Comtrade API request failed: {str(e)}")

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=f"Comtrade API error: {resp.text}")

    return resp.json()


# ---------------------------------------------------------------------------
# data.gov.in — government budget / scheme data (needs free key)
# ---------------------------------------------------------------------------
@app.get("/api/datagovin/{resource_id}")
async def datagovin_resource(resource_id: str, limit: int = 100, offset: int = 0):
    if not DATA_GOV_IN_KEY:
        raise HTTPException(
            status_code=503,
            detail=(
                "DATA_GOV_IN_KEY not set. Register a free key at "
                "https://data.gov.in/apis and add it to backend/.env"
            ),
        )

    url = f"https://api.data.gov.in/resource/{resource_id}"
    params = {
        "api-key": DATA_GOV_IN_KEY,
        "format": "json",
        "limit": limit,
        "offset": offset,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url, params=params)

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="data.gov.in API error")

    return resp.json()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
