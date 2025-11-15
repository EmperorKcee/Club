from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort, send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, Product, ProductCategory, ProductImage
from datetime import datetime
import os
import uuid

shop_admin = Blueprint('shop_admin', __name__, url_prefix='/admin/shop')

@shop_admin.before_request
@login_required
def require_admin():
    if not current_user.is_authenticated or current_user.role != 'admin':
        return redirect(url_for('unauthorized'))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

def save_product_image(file, product_id):
    if not file or file.filename == '':
        return None
        
    if not allowed_file(file.filename):
        return None
        
    # Create upload folder if it doesn't exist
    upload_folder = os.path.join(current_app.static_folder, 'uploads', 'products', str(product_id))
    os.makedirs(upload_folder, exist_ok=True)
    
    # Generate a unique filename
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(upload_folder, filename)
    
    # Save the file
    file.save(filepath)
    
    # Return the relative path for web access
    return os.path.join('uploads', 'products', str(product_id), filename).replace('\\', '/')

@shop_admin.route('/')
@shop_admin.route('/dashboard')
@login_required
def dashboard():
    """Shop admin dashboard"""
    stats = {
        'products_count': Product.query.count(),
        'categories_count': ProductCategory.query.count(),
        'active_products': Product.query.filter_by(is_active=True).count(),
        'out_of_stock': Product.query.filter(Product.stock_quantity <= 0).count()
    }
    
    # Get recent products
    recent_products = Product.query.order_by(Product.created_at.desc()).limit(5).all()
    
    return render_template('admin/shop/dashboard.html', 
                         stats=stats,
                         recent_products=recent_products,
                         Product=Product,
                         ProductCategory=ProductCategory)

@shop_admin.route('/products')
@login_required
def products():
    """List all products"""
    all_products = Product.query.order_by(Product.created_at.desc()).all()
    return render_template('admin/shop/products.html', 
                         products=all_products,
                         Product=Product,
                         ProductCategory=ProductCategory)

@shop_admin.route('/products/new', methods=['GET', 'POST'])
@login_required
def new_product():
    """Create a new product"""
    categories = ProductCategory.query.filter_by(is_active=True).all()
    
    if request.method == 'POST':
        # Handle form submission
        name = request.form.get('name')
        description = request.form.get('description')
        price = float(request.form.get('price', 0))
        sale_price = float(request.form.get('sale_price', 0)) if request.form.get('sale_price') else None
        category_id = int(request.form.get('category_id'))
        sku = request.form.get('sku')
        stock_quantity = int(request.form.get('stock_quantity', 0))
        is_featured = 'is_featured' in request.form
        is_active = 'is_active' in request.form
        
        # Create slug from name
        slug = name.lower().replace(' ', '-')
        
        # Create product
        product = Product(
            name=name,
            slug=slug,
            description=description,
            price=price,
            sale_price=sale_price,
            sku=sku,
            stock_quantity=stock_quantity,
            category_id=category_id,
            is_featured=is_featured,
            is_active=is_active
        )
        
        db.session.add(product)
        db.session.commit()
        
        # Handle image uploads
        if 'images' in request.files:
            for i, file in enumerate(request.files.getlist('images')):
                if file.filename == '':
                    continue
                    
                image_path = save_product_image(file, product.id)
                if image_path:
                    is_main = (i == 0)  # First image is main by default
                    product_image = ProductImage(
                        product_id=product.id,
                        image_url=image_path,
                        alt_text=f"{product.name} - Image {i+1}",
                        is_main=is_main
                    )
                    db.session.add(product_image)
            
            db.session.commit()
        
        flash('Product created successfully!', 'success')
        return redirect(url_for('shop_admin.products'))
    
    return render_template('admin/shop/product_form.html', 
                         title='Add New Product',
                         categories=categories,
                         Product=Product,
                         ProductCategory=ProductCategory)

@shop_admin.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    """Edit an existing product"""
    product = Product.query.get_or_404(product_id)
    categories = ProductCategory.query.filter_by(is_active=True).all()
    
    if request.method == 'POST':
        # Update product details
        product.name = request.form.get('name')
        product.description = request.form.get('description')
        product.price = float(request.form.get('price', 0))
        product.sale_price = float(request.form.get('sale_price', 0)) if request.form.get('sale_price') else None
        product.category_id = int(request.form.get('category_id'))
        product.sku = request.form.get('sku')
        product.stock_quantity = int(request.form.get('stock_quantity', 0))
        product.is_featured = 'is_featured' in request.form
        product.is_active = 'is_active' in request.form
        product.slug = product.name.lower().replace(' ', '-')
        
        # Handle image uploads
        if 'images' in request.files:
            for i, file in enumerate(request.files.getlist('images')):
                if file.filename == '':
                    continue
                    
                image_path = save_product_image(file, product.id)
                if image_path:
                    is_main = (i == 0 and not product.images)  # First image is main if no images exist
                    product_image = ProductImage(
                        product_id=product.id,
                        image_url=image_path,
                        alt_text=f"{product.name} - Image {len(product.images) + i + 1}",
                        is_main=is_main
                    )
                    db.session.add(product_image)
        
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('shop_admin.products'))
    
    return render_template('admin/shop/product_form.html', 
                         title='Edit Product',
                         product=product,
                         categories=categories,
                         Product=Product,
                         ProductCategory=ProductCategory)

@shop_admin.route('/products/<int:product_id>/delete', methods=['POST'])
@login_required
def delete_product(product_id):
    """Delete a product"""
    product = Product.query.get_or_404(product_id)
    
    # Delete product images from filesystem
    for image in product.images:
        try:
            file_path = os.path.join(current_app.static_folder, image.image_url)
            if os.path.exists(file_path):
                os.remove(file_path)
            # Remove the directory if empty
            dir_path = os.path.dirname(file_path)
            if os.path.exists(dir_path) and not os.listdir(dir_path):
                os.rmdir(dir_path)
        except Exception as e:
            current_app.logger.error(f"Error deleting product image: {str(e)}")
    
    db.session.delete(product)
    db.session.commit()
    
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('shop_admin.products'))

@shop_admin.route('/products/<int:product_id>/image/<int:image_id>/delete', methods=['POST'])
@login_required
def delete_product_image(product_id, image_id):
    """Delete a product image"""
    image = ProductImage.query.get_or_404(image_id)
    
    # Delete the image file
    try:
        file_path = os.path.join(current_app.static_folder, image.image_url)
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        current_app.logger.error(f"Error deleting image file: {str(e)}")
    
    # Delete the image record
    db.session.delete(image)
    db.session.commit()
    
    flash('Image deleted successfully!', 'success')
    return redirect(url_for('shop_admin.edit_product', product_id=product_id))

@shop_admin.route('/products/<int:product_id>/image/<int:image_id>/set-main', methods=['POST'])
@login_required
def set_main_image(product_id, image_id):
    """Set an image as the main product image"""
    # Reset all images for this product to not be main
    ProductImage.query.filter_by(product_id=product_id).update({'is_main': False})
    
    # Set the selected image as main
    image = ProductImage.query.get_or_404(image_id)
    image.is_main = True
    
    db.session.commit()
    
    flash('Main image updated successfully!', 'success')
    return redirect(url_for('shop_admin.edit_product', product_id=product_id))

@shop_admin.route('/categories')
@login_required
def categories():
    """List all product categories"""
    all_categories = ProductCategory.query.order_by(ProductCategory.name).all()
    return render_template('admin/shop/categories.html', 
                         categories=all_categories,
                         Product=Product,
                         ProductCategory=ProductCategory)

@shop_admin.route('/categories/new', methods=['GET', 'POST'])
@login_required
def new_category():
    """Create a new product category"""
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        is_active = 'is_active' in request.form
        
        # Create slug from name
        slug = name.lower().replace(' ', '-')
        
        category = ProductCategory(
            name=name,
            slug=slug,
            description=description,
            is_active=is_active
        )
        
        db.session.add(category)
        db.session.commit()
        
        flash('Category created successfully!', 'success')
        return redirect(url_for('shop_admin.categories'))
    
    return render_template('admin/shop/category_form.html', 
                         title='Add New Category',
                         Product=Product,
                         ProductCategory=ProductCategory)

@shop_admin.route('/categories/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_category(category_id):
    """Edit an existing product category"""
    category = ProductCategory.query.get_or_404(category_id)
    
    if request.method == 'POST':
        category.name = request.form.get('name')
        category.description = request.form.get('description')
        category.is_active = 'is_active' in request.form
        category.slug = category.name.lower().replace(' ', '-')
        
        db.session.commit()
        
        flash('Category updated successfully!', 'success')
        return redirect(url_for('shop_admin.categories'))
    
    return render_template('admin/shop/category_form.html', 
                         title='Edit Category',
                         category=category,
                         Product=Product,
                         ProductCategory=ProductCategory)

@shop_admin.route('/categories/<int:category_id>/delete', methods=['POST'])
@login_required
def delete_category(category_id):
    """Delete a product category"""
    category = ProductCategory.query.get_or_404(category_id)
    
    # Check if there are products in this category
    if category.products.count() > 0:
        flash('Cannot delete category with products. Please remove or reassign products first.', 'danger')
        return redirect(url_for('shop_admin.categories'))
    
    db.session.delete(category)
    db.session.commit()
    
    flash('Category deleted successfully!', 'success')
    return redirect(url_for('shop_admin.categories'))

@shop_admin.route('/uploads/products/<int:product_id>/<filename>')
def uploaded_product_image(product_id, filename):
    """Serve uploaded product images"""
    upload_folder = os.path.join(current_app.static_folder, 'uploads', 'products', str(product_id))
    return send_from_directory(upload_folder, filename)
