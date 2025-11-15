import sys
import os

# Set console output encoding to UTF-8
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from app import app, db
from models import Product, ProductCategory, TeamSettings
from sqlalchemy import text

def test_database_connection():
    with app.app_context():
        try:
            # Test database connection
            db.session.execute(text('SELECT 1'))
            db.session.commit()
            print("[OK] Database connection successful")
            
            # Test TeamSettings
            settings = TeamSettings.get_settings()
            print(f"[OK] Team settings: {settings.team_name if settings else 'None'}")
            
            # Test ProductCategory
            categories = ProductCategory.query.all()
            print(f"[OK] Found {len(categories)} categories")
            
            # Test Products
            products = Product.query.all()
            print(f"[OK] Found {len(products)} products")
            
            # Print first 5 products for verification
            for i, product in enumerate(products[:5], 1):
                print(f"  {i}. {product.name} (ID: {product.id}, Price: {product.price})")
                
        except Exception as e:
            error_msg = str(e).replace('\n', ' ').replace('\r', '')  # Clean up error message
            print(f"[ERROR] {error_msg}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    test_database_connection()
