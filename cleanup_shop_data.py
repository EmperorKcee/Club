from app import app, db
from models import Product, ProductCategory, ProductImage
import os

def cleanup_shop_data():
    with app.app_context():
        print("Cleaning up shop data...")
        
        # Delete all products and their images
        products = Product.query.all()
        for product in products:
            print(f"Deleting product: {product.name}")
            
            # Delete product images from filesystem
            for image in product.images:
                try:
                    if image.image_url:
                        file_path = os.path.join(app.static_folder, image.image_url)
                        if os.path.exists(file_path):
                            os.remove(file_path)
                            print(f"  - Deleted image: {file_path}")
                except Exception as e:
                    print(f"  - Error deleting image: {e}")
            
            # Delete product from database
            db.session.delete(product)
        
        # Delete all categories (only if they have no products)
        categories = ProductCategory.query.all()
        for category in categories:
            if not category.products:
                print(f"Deleting unused category: {category.name}")
                db.session.delete(category)
            else:
                print(f"Keeping category (has products): {category.name}")
        
        # Commit changes
        db.session.commit()
        print("Cleanup complete!")

if __name__ == "__main__":
    cleanup_shop_data()
