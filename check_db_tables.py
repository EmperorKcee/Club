from app import app, db
from models import Product, ProductCategory, TeamSettings

def check_tables():
    with app.app_context():
        try:
            # Check if tables exist
            print("Checking database tables...")
            
            # Check TeamSettings table
            print("\nTeamSettings:")
            settings = TeamSettings.get_settings()
            print(f"- Found team settings: {settings.team_name if settings else 'None'}")
            
            # Check ProductCategory table
            print("\nProduct Categories:")
            categories = ProductCategory.query.all()
            print(f"- Found {len(categories)} categories")
            for cat in categories:
                print(f"  - {cat.name} (ID: {cat.id}, Active: {cat.is_active})")
            
            # Check Products table
            print("\nProducts:")
            products = Product.query.all()
            print(f"- Found {len(products)} products")
            for prod in products:
                print(f"  - {prod.name} (ID: {prod.id}, Price: {prod.price}, Stock: {prod.stock_quantity})")
            
            # Check ProductImage table
            from models import ProductImage
            print("\nProduct Images:")
            images = ProductImage.query.all()
            print(f"- Found {len(images)} product images")
            
        except Exception as e:
            print(f"\nError: {str(e)}")
            print("\nThis error suggests there might be an issue with the database tables.")
            print("Please run the following command to create the database tables:")
            print("python -c 'from app import app, db; with app.app_context(): db.create_all()'")

if __name__ == "__main__":
    check_tables()
