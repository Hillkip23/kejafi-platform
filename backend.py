# backend.py - Clean API for Kejafi Workspace
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import json
from pathlib import Path

app = FastAPI(title="Kejafi API", version="1.0.1")

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

class PropertyCreate(BaseModel):
    id: str
    address: str
    county: Optional[str] = None
    metro: Optional[str] = None
    list_price: float
    token_symbol: str
    token_address: str
    pool_address: Optional[str] = None

@app.get("/")
def root():
    return {"message": "Kejafi API Running", "workspace": "Kejafi_Workspace"}

@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/properties")
def get_properties():
    return list(properties_db.values())

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
    print("=" * 50)
    print("?? Kejafi API Running")
    print("?? http://localhost:8000")
    print("=" * 50)
    uvicorn.run(app, host="127.0.0.1", port=8000)
