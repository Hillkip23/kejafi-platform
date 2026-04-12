# backend.py - Clean API for Kejafi Workspace
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import json
from pathlib import Path
import os

app = FastAPI(title="Kejafi API", version="1.0.3")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "api_data"
DATA_DIR.mkdir(exist_ok=True)

properties_db = {}

def load_data():
    global properties_db
    prop_file = DATA_DIR / "properties.json"
    if prop_file.exists():
        with open(prop_file, 'r') as f:
            properties_db = json.load(f)

def save_data():
    with open(DATA_DIR / "properties.json", 'w') as f:
        json.dump(properties_db, f, indent=2)

load_data()

# Complete model matching stage2.py payload
class PropertyCreate(BaseModel):
    id: str
    address: str
    county: Optional[str] = None
    metro: Optional[str] = None
    list_price: float
    noi: Optional[float] = None
    cap_rate: Optional[float] = None
    irr: Optional[float] = None
    equity_multiple: Optional[float] = None
    token_symbol: str
    token_address: str
    token_price: Optional[float] = None
    total_supply: Optional[int] = 100000
    lockup_months: Optional[int] = 12
    pool_address: Optional[str] = None
    chain_id: Optional[int] = 11155111
    pci_2023: Optional[float] = None
    pop_growth: Optional[float] = None
    risk_score: Optional[float] = None
    risk_bucket: Optional[str] = None
    supply_bucket: Optional[str] = None
    metro_elasticity: Optional[float] = None
    nav_total: Optional[float] = None
    nav_per_token: Optional[float] = None
    nav_currency: Optional[str] = "USD"
    amm: Optional[str] = "uniswap_v3"
    quote_asset: Optional[str] = "USDC"
    initial_price: Optional[float] = None
    seed_token_amount: Optional[int] = None
    seed_quote_amount: Optional[float] = None
    fee_tier: Optional[float] = 0.003
    price_range_low: Optional[float] = None
    price_range_high: Optional[float] = None
    created_at: Optional[str] = None

@app.get("/")
def root():
    return {"message": "Kejafi API Running", "version": "1.0.2"}

@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/properties")
def get_properties():
    return list(properties_db.values())

@app.get("/properties/{property_id}")
def get_property(property_id: str):
    if property_id not in properties_db:
        raise HTTPException(status_code=404, detail="Property not found")
    return properties_db[property_id]

@app.post("/properties")
def create_property(prop: PropertyCreate):
    prop_dict = prop.model_dump()
    prop_dict["created_at"] = datetime.now().isoformat()
    properties_db[prop.id] = prop_dict
    save_data()
    return {"status": "success", "property": prop_dict}

@app.get("/contracts")
def get_contracts():
    return {
        "pool_address": "0x0Bf78f76c86153E433dAA5Ac6A88453D30968e27",
        "fine5_address": "0x0FB987BEE67FD839cb1158B0712d5e4Be483dd2E",
        "fine6_address": "0xe051C1eA47b246c79f3bac4e58E459cF2Aa20692",
        "chain_id": 11155111
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print("=" * 50)
    print("?? Kejafi API Running")
    print(f"?? Port: {port}")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=port)
