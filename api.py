from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import random
from datetime import datetime, timedelta

app = FastAPI()

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins, restrict this in production
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


# Function to generate random shirt data
def generate_random_shirt_data(count=5):
    products = []

    # Design styles
    design_styles = [
        "Modern",
        "Classic",
        "Minimal",
        "Vintage",
        "Abstract",
        "Geometric",
        "Floral",
        "Industrial",
        "Scandinavian",
        "Bohemian",
        "Rustic",
        "Contemporary",
        "Eclectic",
        "Art Deco",
        "Retro",
        "Futuristic",
        "Baroque",
        "Gothic",
        "Tropical",
        "Nautical",
        "Urban",
        "Traditional",
        "Mid-Century",
        "Pop Art",
        "Country",
        "Shabby Chic",
        "Oriental",
        "Mediterranean",
        "Victorian",
        "Zen",
        "",
    ]

    # Email domains
    email_domains = [
        "gmail.com",
        "yahoo.com",
        "outlook.com",
        "hotmail.com",
        "example.com",
        "company.com",
        "business.org",
        "mail.net",
        "custom.io",
    ]

    # Start date for generation
    start_date = datetime.now()

    for i in range(1, count + 1):
        # Generate random id (simulating database increment)
        item_id = random.randint(1, 1000)

        # Randomly select product type
        product_type = random.choice(["Shirt", "T-Shirt"])

        # Generate a random date between 2 days ago and today
        random_days = random.randint(-2, 0)
        random_date = (start_date + timedelta(days=random_days)).strftime("%Y-%m-%d")

        # Random design
        design = random.choice(design_styles)

        # Random fastShip boolean (as string)
        fast_ship = random.choice(["True", "False", "Fasle"])

        # Random quantity between 1 and 20
        quantity = random.randint(1, 20)

        # Generate random email
        email_prefix = f"user{random.randint(100, 999)}"
        email_domain = random.choice(email_domains)
        email = f"{email_prefix}@{email_domain}"

        # Create the product dictionary
        product = {
            "id": item_id,
            "product": product_type,
            "date": random_date,
            "design": design,
            "fastShip": fast_ship,
            "quantity": quantity,
            "mail": email,
        }

        products.append(product)

    return products


# API endpoint - returns 1-5 random items
@app.get("/api/get_data")
async def get_data():
    try:
        # Generate random number of items between 1 and 5
        count = random.randint(1, 5)
        data = generate_random_shirt_data(count)

        return JSONResponse(content={"status": "success", "data": data})
    except Exception as e:
        return JSONResponse(content={"status": "error", "message": str(e)})


# API endpoint that returns a specific amount of data
@app.get("/api/get_data/{amount}")
async def get_random_data(amount: int):
    try:
        # Limit amount to reasonable range
        if amount < 1:
            amount = 1
        elif amount > 50:  # Set a reasonable upper limit
            amount = 50

        data = generate_random_shirt_data(amount)

        return JSONResponse(content={"status": "success", "data": data})
    except Exception as e:
        return JSONResponse(content={"status": "error", "message": str(e)})


# Root endpoint for testing
@app.get("/")
async def root():
    return JSONResponse(
        content={
            "message": "Shirt API is running. Use /api/get_data to get random shirt data."
        }
    )
