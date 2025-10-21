import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

async def seed_pos_data():
    """Seed initial POS data"""
    
    # Product Categories
    categories = [
        {
            "id": "cat_cold_drinks",
            "name": "Cold Drinks",
            "description": "Soft drinks, water, sports drinks",
            "display_order": 1,
            "icon": "droplet",
            "is_active": True
        },
        {
            "id": "cat_hot_drinks",
            "name": "Hot Drinks",
            "description": "Coffee, tea, hot chocolate",
            "display_order": 2,
            "icon": "coffee",
            "is_active": True
        },
        {
            "id": "cat_snacks",
            "name": "Snacks",
            "description": "Protein bars, chips, nuts",
            "display_order": 3,
            "icon": "cookie",
            "is_active": True
        },
        {
            "id": "cat_supplements",
            "name": "Supplements",
            "description": "Protein powder, pre-workout, vitamins",
            "display_order": 4,
            "icon": "pill",
            "is_active": True
        },
        {
            "id": "cat_merchandise",
            "name": "Merchandise",
            "description": "Branded apparel, accessories",
            "display_order": 5,
            "icon": "shirt",
            "is_active": True
        }
    ]
    
    # Check if categories already exist
    existing_cats = await db.product_categories.count_documents({})
    if existing_cats == 0:
        await db.product_categories.insert_many(categories)
        print(f"✅ Seeded {len(categories)} product categories")
    else:
        print(f"ℹ️  Product categories already exist ({existing_cats} found)")
    
    # Sample Products
    products = [
        # Cold Drinks
        {
            "id": "prod_water_500ml",
            "name": "Water 500ml",
            "sku": "WAT500",
            "category_id": "cat_cold_drinks",
            "category_name": "Cold Drinks",
            "cost_price": 5.00,
            "markup_percent": 100.0,
            "selling_price": 10.00,
            "tax_rate": 15.0,
            "stock_quantity": 100,
            "low_stock_threshold": 20,
            "description": "Still mineral water",
            "is_favorite": True,
            "is_active": True
        },
        {
            "id": "prod_energade",
            "name": "Energade 500ml",
            "sku": "ENG500",
            "category_id": "cat_cold_drinks",
            "category_name": "Cold Drinks",
            "cost_price": 12.00,
            "markup_percent": 66.67,
            "selling_price": 20.00,
            "tax_rate": 15.0,
            "stock_quantity": 50,
            "low_stock_threshold": 15,
            "description": "Sports drink",
            "is_favorite": True,
            "is_active": True
        },
        {
            "id": "prod_coke_330ml",
            "name": "Coke 330ml",
            "sku": "COKE330",
            "category_id": "cat_cold_drinks",
            "category_name": "Cold Drinks",
            "cost_price": 8.00,
            "markup_percent": 87.5,
            "selling_price": 15.00,
            "tax_rate": 15.0,
            "stock_quantity": 75,
            "low_stock_threshold": 20,
            "description": "Coca-Cola can",
            "is_favorite": False,
            "is_active": True
        },
        # Hot Drinks
        {
            "id": "prod_coffee",
            "name": "Coffee",
            "sku": "COFFEE",
            "category_id": "cat_hot_drinks",
            "category_name": "Hot Drinks",
            "cost_price": 5.00,
            "markup_percent": 200.0,
            "selling_price": 15.00,
            "tax_rate": 15.0,
            "stock_quantity": 200,
            "low_stock_threshold": 30,
            "description": "Filter coffee",
            "is_favorite": True,
            "is_active": True
        },
        # Snacks
        {
            "id": "prod_protein_bar",
            "name": "Protein Bar",
            "sku": "PROBAR",
            "category_id": "cat_snacks",
            "category_name": "Snacks",
            "cost_price": 15.00,
            "markup_percent": 100.0,
            "selling_price": 30.00,
            "tax_rate": 15.0,
            "stock_quantity": 100,
            "low_stock_threshold": 25,
            "description": "High protein snack bar",
            "is_favorite": True,
            "is_active": True
        },
        {
            "id": "prod_banana",
            "name": "Banana",
            "sku": "BANANA",
            "category_id": "cat_snacks",
            "category_name": "Snacks",
            "cost_price": 3.00,
            "markup_percent": 100.0,
            "selling_price": 6.00,
            "tax_rate": 15.0,
            "stock_quantity": 50,
            "low_stock_threshold": 10,
            "description": "Fresh banana",
            "is_favorite": True,
            "is_active": True
        },
        # Supplements
        {
            "id": "prod_whey_protein_1kg",
            "name": "Whey Protein 1kg",
            "sku": "WHEY1KG",
            "category_id": "cat_supplements",
            "category_name": "Supplements",
            "cost_price": 300.00,
            "markup_percent": 50.0,
            "selling_price": 450.00,
            "tax_rate": 15.0,
            "stock_quantity": 20,
            "low_stock_threshold": 5,
            "description": "Whey protein powder 1kg",
            "is_favorite": False,
            "is_active": True
        },
        {
            "id": "prod_preworkout",
            "name": "Pre-Workout",
            "sku": "PREWORK",
            "category_id": "cat_supplements",
            "category_name": "Supplements",
            "cost_price": 250.00,
            "markup_percent": 60.0,
            "selling_price": 400.00,
            "tax_rate": 15.0,
            "stock_quantity": 15,
            "low_stock_threshold": 5,
            "description": "Pre-workout supplement",
            "is_favorite": False,
            "is_active": True
        },
        # Merchandise
        {
            "id": "prod_gym_tshirt",
            "name": "Gym T-Shirt",
            "sku": "TSHIRT",
            "category_id": "cat_merchandise",
            "category_name": "Merchandise",
            "cost_price": 80.00,
            "markup_percent": 87.5,
            "selling_price": 150.00,
            "tax_rate": 15.0,
            "stock_quantity": 30,
            "low_stock_threshold": 10,
            "description": "Branded gym t-shirt",
            "is_favorite": False,
            "is_active": True
        },
        {
            "id": "prod_gym_towel",
            "name": "Gym Towel",
            "sku": "TOWEL",
            "category_id": "cat_merchandise",
            "category_name": "Merchandise",
            "cost_price": 40.00,
            "markup_percent": 75.0,
            "selling_price": 70.00,
            "tax_rate": 15.0,
            "stock_quantity": 40,
            "low_stock_threshold": 10,
            "description": "Gym towel",
            "is_favorite": False,
            "is_active": True
        }
    ]
    
    # Check if products already exist
    existing_products = await db.products.count_documents({})
    if existing_products == 0:
        await db.products.insert_many(products)
        print(f"✅ Seeded {len(products)} sample products")
    else:
        print(f"ℹ️  Products already exist ({existing_products} found)")
    
    print("\n✅ POS system seeded successfully!")
    print("\nDefault Product Categories:")
    for cat in categories:
        print(f"  - {cat['name']}")
    print(f"\nSample Products: {len(products)} products created")

if __name__ == "__main__":
    asyncio.run(seed_pos_data())
    print("\nDone!")
