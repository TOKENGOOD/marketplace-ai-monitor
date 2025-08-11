from datetime import datetime, timezone

def fetch_mock_results():
    now = datetime.now(timezone.utc).isoformat()
    return [
        {
            "title": "Apple iPhone 13 128GB — Great condition",
            "price_cents": 25000,
            "url": "https://www.facebook.com/marketplace/item/mock-iphone-13-128",
            "created_at": now,
        },
        {
            "title": "Samsung Galaxy S21 256GB — Mint",
            "price_cents": 23000,
            "url": "https://www.facebook.com/marketplace/item/mock-s21-256",
            "created_at": now,
        },
        {
            "title": "iPhone 12 64GB — OK battery",
            "price_cents": 18000,
            "url": "https://www.facebook.com/marketplace/item/mock-iphone-12",
            "created_at": now,
        },
        {
            "title": "PlayStation 5 Disc Edition — New Sealed",
            "price_cents": 40000,
            "url": "https://www.facebook.com/marketplace/item/mock-ps5",
            "created_at": now,
        },
    ]
