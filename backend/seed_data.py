#!/usr/bin/env python3
"""Seed initial data for the gym management system"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path
import uuid
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

async def seed_data():
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    db_name = os.environ['DB_NAME']
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # Check if membership types already exist
    existing_types = await db.membership_types.count_documents({})
    if existing_types > 0:
        print(f"Found {existing_types} existing membership types. Skipping seed.")
        return
    
    # Create default membership types
    membership_types = [
        {
            "id": str(uuid.uuid4()),
            "name": "Basic Monthly",
            "description": "Basic gym access with standard equipment",
            "price": 299.00,
            "billing_frequency": "monthly",
            "duration_months": 1,
            "features": ["Gym access during peak hours", "Basic equipment", "Locker"],
            "peak_hours_only": True,
            "multi_site_access": False,
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Premium Monthly",
            "description": "Full gym access with all amenities",
            "price": 599.00,
            "billing_frequency": "monthly",
            "duration_months": 1,
            "features": ["24/7 gym access", "All equipment", "Group classes", "Locker", "Sauna"],
            "peak_hours_only": False,
            "multi_site_access": True,
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "6-Month Package",
            "description": "6-month commitment with discounted rate",
            "price": 3200.00,
            "billing_frequency": "6months",
            "duration_months": 6,
            "features": ["24/7 gym access", "All equipment", "Group classes", "Personal trainer session", "Nutrition consultation"],
            "peak_hours_only": False,
            "multi_site_access": True,
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Annual Membership",
            "description": "Best value - annual membership",
            "price": 5999.00,
            "billing_frequency": "yearly",
            "duration_months": 12,
            "features": ["24/7 gym access", "All equipment", "Unlimited group classes", "Monthly personal trainer session", "Nutrition plan", "Priority booking"],
            "peak_hours_only": False,
            "multi_site_access": True,
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Day Pass",
            "description": "Single day access",
            "price": 50.00,
            "billing_frequency": "one-time",
            "duration_months": 0,
            "features": ["Single day access", "Basic equipment"],
            "peak_hours_only": False,
            "multi_site_access": False,
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    # Insert membership types
    await db.membership_types.insert_many(membership_types)
    print(f"✅ Created {len(membership_types)} membership types")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_data())
