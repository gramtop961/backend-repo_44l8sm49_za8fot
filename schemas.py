"""
Database Schemas for Calciomercato Social (LinkedIn for Footballers)

Each Pydantic model represents a MongoDB collection.
Collection name is the lowercase of the class name.
"""
from pydantic import BaseModel, Field
from typing import Optional, List

class Player(BaseModel):
    """Players collection schema -> collection: "player""" 
    name: str = Field(..., description="Full name of the player")
    position: str = Field(..., description="Primary position, e.g., Forward, Midfielder")
    age: Optional[int] = Field(None, ge=8, le=60, description="Age of the player")
    nationality: Optional[str] = Field(None, description="Country of origin")
    current_club_id: Optional[str] = Field(None, description="Current club id (string ObjectId)")
    height_cm: Optional[int] = Field(None, ge=100, le=230, description="Height in centimeters")
    preferred_foot: Optional[str] = Field(None, description="Right / Left / Both")
    bio: Optional[str] = Field(None, description="Short biography")
    skills: Optional[List[str]] = Field(default_factory=list, description="Notable skills/tags")
    market_value: Optional[float] = Field(None, ge=0, description="Estimated market value in EUR")

class Club(BaseModel):
    """Clubs collection schema -> collection: "club"""
    name: str = Field(..., description="Club name")
    league: Optional[str] = Field(None, description="League name, e.g., Serie A")
    country: Optional[str] = Field(None, description="Country")
    budget: Optional[float] = Field(0, ge=0, description="Transfer budget in EUR")
    stadium: Optional[str] = Field(None, description="Home stadium")
    bio: Optional[str] = Field(None, description="Club description")

class Transferlisting(BaseModel):
    """Transfer listings posted for players -> collection: "transferlisting"""
    player_id: str = Field(..., description="Player being listed (string ObjectId)")
    from_club_id: Optional[str] = Field(None, description="Current owner club id (string ObjectId)")
    asking_price: float = Field(..., ge=0, description="Asking price in EUR")
    status: str = Field("open", description="open | under_review | closed")

class Transferoffer(BaseModel):
    """Offers made by clubs on a listing -> collection: "transferoffer"""
    listing_id: str = Field(..., description="Related transfer listing id (string ObjectId)")
    club_id: str = Field(..., description="Offering club id (string ObjectId)")
    offer_amount: float = Field(..., ge=0, description="Offer amount in EUR")
    status: str = Field("pending", description="pending | accepted | rejected")
    message: Optional[str] = Field(None, description="Optional message from club")
