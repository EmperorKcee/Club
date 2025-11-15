from app import app, db
from models import Product, ProductCategory, TeamSettings
from flask import render_template, jsonify
from sqlalchemy import text

@app.route('/debug/shop')
def debug_shop():
    response = {
        'status': 'success',
        'data': {}
    }
    status_code = 200
    
    try:
        # Test database connection
        db.session.execute(text('SELECT 1'))
        
        # Get team settings
        team_settings = TeamSettings.get_settings()
        if not team_settings:
            response.update({
                'status': 'error',
                'message': 'Team settings not found',
                'data': None
            })
            return jsonify(response), 404
            
        response['data']['team_name'] = team_settings.team_name
        
        # Get categories
        try:
            categories = ProductCategory.query.filter_by(is_active=True).all()
            response['data']['categories_count'] = len(categories)
        except Exception as e:
            response.update({
                'status': 'partial',
                'message': f'Error fetching categories: {str(e)}',
                'error_type': type(e).__name__
            })
        
        # Get products
        try:
            products = Product.query.filter_by(is_active=True).all()
            response['data']['products_count'] = len(products)
            
            # Add sample products
            response['data']['sample_products'] = [{
                'id': p.id,
                'name': p.name,
                'price': float(p.price) if p.price else None,
                'category_id': p.category_id
            } for p in products[:3]]  # First 3 products as sample
            
        except Exception as e:
            response.update({
                'status': 'partial',
                'message': f'Error fetching products: {str(e)}',
                'error_type': type(e).__name__
            })
        
    except Exception as e:
        response.update({
            'status': 'error',
            'message': str(e),
            'error_type': type(e).__name__,
            'data': None
        })
        status_code = 500
    
    return jsonify(response), status_code

if __name__ == '__main__':
    with app.app_context():
        result, status_code = debug_shop()
        if status_code == 200:
            print(result.get_json())
        else:
            print(f"Error {status_code}:", result.get_json())
