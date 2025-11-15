from app import app, db
from models import Product, ProductCategory, TeamSettings
import os

def init_shop():
    with app.app_context():
        # Create all database tables
        db.create_all()
        
        # Initialize team settings if they don't exist
        if not TeamSettings.query.first():
            team_settings = TeamSettings(
                team_name='Zambia FC',
                logo_url='img/logo.png',
                primary_color='#b11601',
                secondary_color='#f8f9fa',
                text_color='#ffffff',
                contact_email='info@zambiafc.com',
                contact_phone='+260 123 456 789',
                address='123 Soccer Way, Lusaka, Zambia',
                founded_year=2020,
                about='A professional football club based in Zambia'
            )
            db.session.add(team_settings)
            db.session.commit()
            print("Team settings initialized.")
        
        # Create sample categories if none exist
        if not ProductCategory.query.first():
            categories = [
                ProductCategory(name='Jerseys', slug='jerseys', description='Official team jerseys and kits'),
                ProductCategory(name='Apparel', slug='apparel', description='Team-branded clothing and accessories'),
                ProductCategory(name='Accessories', slug='accessories', description='Team-branded accessories'),
                ProductCategory(name='Equipment', slug='equipment', description='Training and match equipment')
            ]
            db.session.add_all(categories)
            db.session.commit()
            print("Sample categories created.")
        
        print("Shop initialization complete.")

if __name__ == '__main__':
    init_shop()
