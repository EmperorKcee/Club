from app import app, db
from models import Product, ProductCategory, ProductImage
from datetime import datetime

def add_sample_products():
    with app.app_context():
        try:
            # Get existing categories
            categories = ProductCategory.query.all()
            if not categories:
                print("No categories found. Please run the init_shop.py script first.")
                return
                
            print("Adding sample products...")
            
            # Sample products data
            sample_products = [
                {
                    'name': 'Home Jersey 2024',
                    'description': 'Official home jersey for the 2024 season',
                    'price': 299.99,
                    'sale_price': 249.99,
                    'stock_quantity': 50,
                    'category': 'Jerseys',
                    'is_featured': True,
                    'images': [
                        {'url': 'img/products/jersey-home-2024.jpg', 'is_main': True, 'alt': 'Home Jersey 2024'}
                    ]
                },
                {
                    'name': 'Away Jersey 2024',
                    'description': 'Official away jersey for the 2024 season',
                    'price': 299.99,
                    'stock_quantity': 30,
                    'category': 'Jerseys',
                    'is_featured': True,
                    'images': [
                        {'url': 'img/products/jersey-away-2024.jpg', 'is_main': True, 'alt': 'Away Jersey 2024'}
                    ]
                },
                {
                    'name': 'Team Scarf',
                    'description': 'Official team scarf - perfect for match days',
                    'price': 49.99,
                    'stock_quantity': 100,
                    'category': 'Accessories',
                    'is_featured': True,
                    'images': [
                        {'url': 'img/products/scarf.jpg', 'is_main': True, 'alt': 'Team Scarf'}
                    ]
                },
                {
                    'name': 'Team Cap',
                    'description': 'Official team cap with logo embroidery',
                    'price': 39.99,
                    'stock_quantity': 75,
                    'category': 'Accessories',
                    'images': [
                        {'url': 'img/products/cap.jpg', 'is_main': True, 'alt': 'Team Cap'}
                    ]
                },
                {
                    'name': 'Training T-Shirt',
                    'description': 'Comfortable training t-shirt with team logo',
                    'price': 79.99,
                    'stock_quantity': 60,
                    'category': 'Apparel',
                    'images': [
                        {'url': 'img/products/tshirt.jpg', 'is_main': True, 'alt': 'Training T-Shirt'}
                    ]
                },
                {
                    'name': 'Team Hoodie',
                    'description': 'Warm hoodie with team colors and logo',
                    'price': 129.99,
                    'sale_price': 99.99,
                    'stock_quantity': 40,
                    'category': 'Apparel',
                    'is_featured': True,
                    'images': [
                        {'url': 'img/products/hoodie.jpg', 'is_main': True, 'alt': 'Team Hoodie'}
                    ]
                },
                {
                    'name': 'Team Football',
                    'description': 'Official match football',
                    'price': 199.99,
                    'stock_quantity': 25,
                    'category': 'Equipment',
                    'images': [
                        {'url': 'img/products/football.jpg', 'is_main': True, 'alt': 'Team Football'}
                    ]
                },
                {
                    'name': 'Goalkeeper Gloves',
                    'description': 'Professional goalkeeper gloves',
                    'price': 149.99,
                    'stock_quantity': 20,
                    'category': 'Equipment',
                    'images': [
                        {'url': 'img/products/gloves.jpg', 'is_main': True, 'alt': 'Goalkeeper Gloves'}
                    ]
                }
            ]
            
            # Add sample products
            for product_data in sample_products:
                # Find the category
                category = next((c for c in categories if c.name == product_data['category']), None)
                if not category:
                    print(f"Category '{product_data['category']}' not found. Skipping product: {product_data['name']}")
                    continue
                
                # Create product
                product = Product(
                    name=product_data['name'],
                    slug=product_data['name'].lower().replace(' ', '-') + '-2024',
                    description=product_data['description'],
                    price=product_data['price'],
                    sale_price=product_data.get('sale_price'),
                    stock_quantity=product_data['stock_quantity'],
                    category_id=category.id,
                    is_featured=product_data.get('is_featured', False),
                    is_active=True
                )
                
                # Add product to session
                db.session.add(product)
                db.session.flush()  # Get the product ID for images
                
                # Add product images
                for img_data in product_data.get('images', []):
                    img = ProductImage(
                        product_id=product.id,
                        image_url=img_data['url'],
                        alt_text=img_data['alt'],
                        is_main=img_data.get('is_main', False)
                    )
                    db.session.add(img)
                
                print(f"Added product: {product.name}")
            
            # Commit all changes
            db.session.commit()
            print("\nSample products added successfully!")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error: {str(e)}")
            raise

if __name__ == "__main__":
    add_sample_products()
