from app import app, db
from models import TeamSettings, ProductCategory, Product, ProductImage

def check_database():
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            
            # Check if team settings exist
            settings = TeamSettings.get_settings()
            print(f"Team settings: {settings.team_name if settings else 'Not found'}")
            
            # Check product categories
            categories = ProductCategory.query.all()
            print(f"Found {len(categories)} product categories")
            
            # Check products
            products = Product.query.all()
            print(f"Found {len(products)} products")
            
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    check_database()
