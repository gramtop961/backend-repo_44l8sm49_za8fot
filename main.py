import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents

app = FastAPI(title="Calciomercato Social API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic response helpers
class IdModel(BaseModel):
    id: str

# Simple serialization helper

def serialize(doc):
    if not doc:
        return doc
    d = dict(doc)
    if "_id" in d:
        d["id"] = str(d.pop("_id"))
    return d

@app.get("/")
def read_root():
    return {"message": "Calciomercato Social Backend Running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Connected & Working"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name
            try:
                response["collections"] = db.list_collection_names()
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    return response

# --- Core domain endpoints ---

# Create player
class PlayerIn(BaseModel):
    name: str
    position: str
    age: Optional[int] = None
    nationality: Optional[str] = None
    current_club_id: Optional[str] = None
    height_cm: Optional[int] = None
    preferred_foot: Optional[str] = None
    bio: Optional[str] = None
    skills: Optional[List[str]] = []
    market_value: Optional[float] = None

@app.post("/players", response_model=IdModel)
def create_player(player: PlayerIn):
    player_dict = player.model_dump()
    new_id = create_document("player", player_dict)
    return {"id": new_id}

@app.get("/players")
def list_players():
    docs = get_documents("player")
    return [serialize(d) for d in docs]

# Create club
class ClubIn(BaseModel):
    name: str
    league: Optional[str] = None
    country: Optional[str] = None
    budget: Optional[float] = 0
    stadium: Optional[str] = None
    bio: Optional[str] = None

@app.post("/clubs", response_model=IdModel)
def create_club(club: ClubIn):
    new_id = create_document("club", club.model_dump())
    return {"id": new_id}

@app.get("/clubs")
def list_clubs():
    docs = get_documents("club")
    return [serialize(d) for d in docs]

# Transfer listing
class ListingIn(BaseModel):
    player_id: str
    from_club_id: Optional[str] = None
    asking_price: float
    status: str = "open"

@app.post("/listings", response_model=IdModel)
def create_listing(listing: ListingIn):
    # basic sanity: player must exist
    if not ObjectId.is_valid(listing.player_id):
        raise HTTPException(status_code=400, detail="Invalid player_id")
    if listing.from_club_id and not ObjectId.is_valid(listing.from_club_id):
        raise HTTPException(status_code=400, detail="Invalid from_club_id")

    # optionally check presence
    player = db["player"].find_one({"_id": ObjectId(listing.player_id)})
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    new_id = create_document("transferlisting", listing.model_dump())
    return {"id": new_id}

@app.get("/listings")
def list_listings():
    docs = db["transferlisting"].aggregate([
        {"$lookup": {"from": "player", "localField": "player_id", "foreignField": "_id", "as": "player"}},
        {"$unwind": "$player"},
        {"$lookup": {"from": "club", "localField": "from_club_id", "foreignField": "_id", "as": "from_club"}},
        {"$unwind": {"path": "$from_club", "preserveNullAndEmptyArrays": True}},
    ])
    res = []
    for d in docs:
        d = serialize(d)
        if "player" in d and "_id" in d["player"]:
            d["player"]["id"] = str(d["player"].pop("_id"))
        if "from_club" in d and d["from_club"] and "_id" in d["from_club"]:
            d["from_club"]["id"] = str(d["from_club"].pop("_id"))
        res.append(d)
    return res

# Transfer offer
class OfferIn(BaseModel):
    listing_id: str
    club_id: str
    offer_amount: float
    status: str = "pending"
    message: Optional[str] = None

@app.post("/offers", response_model=IdModel)
def create_offer(offer: OfferIn):
    if not ObjectId.is_valid(offer.listing_id) or not ObjectId.is_valid(offer.club_id):
        raise HTTPException(status_code=400, detail="Invalid ids")
    if not db["transferlisting"].find_one({"_id": ObjectId(offer.listing_id)}):
        raise HTTPException(status_code=404, detail="Listing not found")
    if not db["club"].find_one({"_id": ObjectId(offer.club_id)}):
        raise HTTPException(status_code=404, detail="Club not found")

    new_id = create_document("transferoffer", offer.model_dump())
    return {"id": new_id}

@app.get("/offers")
def list_offers():
    docs = db["transferoffer"].aggregate([
        {"$lookup": {"from": "transferlisting", "localField": "listing_id", "foreignField": "_id", "as": "listing"}},
        {"$unwind": "$listing"},
        {"$lookup": {"from": "club", "localField": "club_id", "foreignField": "_id", "as": "club"}},
        {"$unwind": "$club"},
    ])
    res = []
    for d in docs:
        d = serialize(d)
        if "listing" in d and "_id" in d["listing"]:
            d["listing"]["id"] = str(d["listing"].pop("_id"))
        if "club" in d and "_id" in d["club"]:
            d["club"]["id"] = str(d["club"].pop("_id"))
        res.append(d)
    return res

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
