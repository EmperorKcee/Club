from flask import Blueprint, render_template, flash, redirect, url_for, request, current_app, abort, jsonify
from flask_login import current_user, login_required
from models import Match, News as NewsArticle, TeamSettings, TrainingSession, db, Ticket, TicketPurchase, FanMessage, Product, ProductCategory, Subscription
from datetime import datetime, timedelta
from sqlalchemy import or_, and_, desc
from werkzeug.security import generate_password_hash
from extensions import socketio  # Import socketio from extensions
import uuid
import os

# Store active users
active_users = {}

# Email validation
import re

def is_valid_email(email):
    """Check if the email address is valid"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def register_socketio_handlers(socketio):
    """Register all socketio event handlers"""
    from flask_socketio import emit, join_room, leave_room
    from flask import request

    @socketio.on('connect')
    def handle_connect():
        """Handle new WebSocket connection"""
        print(f"Client connected: {request.sid}")

    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle WebSocket disconnection"""
        user_id = None
        for uid, sid in active_users.items():
            if sid == request.sid:
                user_id = uid
                break
        if user_id:
            del active_users[user_id]
            emit('user_left', {'user_id': user_id}, broadcast=True)

    @socketio.on('user_join')
    def handle_user_join(data):
        """Handle when a user joins the chat"""
        if not current_user.is_authenticated:
            return
            
        user_id = data.get('user_id')
        username = data.get('username')
        
        if user_id and username and user_id == str(current_user.id) and username == current_user.username:
            active_users[user_id] = request.sid
            emit('user_status', 
                 {'user_id': user_id, 'username': username, 'status': 'online'}, 
                 broadcast=True)
            
            # Send last 50 messages to the user
            messages = FanMessage.query.order_by(FanMessage.created_at.desc()).limit(50).all()
            emit('chat_history', {'messages': [msg.to_dict() for msg in reversed(messages)]})

    @socketio.on('send_message')
    def handle_send_message(data):
        """Handle new chat message"""
        if not current_user.is_authenticated:
            return
            
        user_id = data.get('user_id')
        username = data.get('username')
        message = data.get('message', '').strip()
    
        if not message or user_id != str(current_user.id) or username != current_user.username:
            return
        
        # Create and save the message
        new_message = FanMessage(
            user_id=current_user.id,
            username=current_user.username,
            message=message,
            avatar=current_user.profile_picture if hasattr(current_user, 'profile_picture') else None
        )
        
        db.session.add(new_message)
        db.session.commit()
        
        # Broadcast the new message to all connected clients
        emit('new_message', 
             {'message': new_message.to_dict()}, 
             broadcast=True)

fans_bp = Blueprint('fans', __name__)

@fans_bp.route('/fans/subscribe', methods=['GET'])
def subscribe_page():
    """Render the subscription page"""
    return render_template('fans/subscribe.html')

@fans_bp.route('/fans/subscribe', methods=['POST'])
def subscribe():
    """Handle newsletter subscription"""
    try:
        # Check if this is a form submission or AJAX
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if is_ajax:
            data = request.get_json()
            email = data.get('email', '').strip()
            name = data.get('name', '').strip()
        else:
            email = request.form.get('email', '').strip()
            name = request.form.get('name', '').strip()

        # Validate email
        if not email or not is_valid_email(email):
            if is_ajax:
                return jsonify({
                    'success': False,
                    'message': 'Please provide a valid email address.'
                }), 400
            flash('Please provide a valid email address.', 'danger')
            return redirect(url_for('fans.subscribe_page'))

        # Check if email already exists
        subscription = Subscription.query.filter_by(email=email).first()

        if subscription:
            if subscription.is_active:
                if is_ajax:
                    return jsonify({
                        'success': False,
                        'message': 'This email is already subscribed.'
                    }), 400
                flash('This email is already subscribed.', 'warning')
                return redirect(url_for('fans.subscribe_page'))
            else:
                # Reactivate existing subscription
                subscription.is_active = True
                subscription.subscribed_at = datetime.utcnow()
                subscription.unsubscribed_at = None
                if name:
                    subscription.name = name
                db.session.commit()
                
                if is_ajax:
                    return jsonify({
                        'success': True,
                        'message': 'Successfully resubscribed to our newsletter!'
                    })
                flash('Successfully resubscribed to our newsletter!', 'success')
                return redirect(url_for('fans.subscribe_page'))
        
        # Create new subscription
        new_subscription = Subscription(
            email=email,
            name=name if name else None,
            is_active=True,
            subscribed_at=datetime.utcnow()
        )
        
        db.session.add(new_subscription)
        db.session.commit()
        
        if is_ajax:
            return jsonify({
                'success': True,
                'message': 'Thank you for subscribing to our newsletter!'
            })
            
        flash('Thank you for subscribing to our newsletter!', 'success')
        return redirect(url_for('fans.subscribe_page'))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Subscription error: {str(e)}')
        if is_ajax:
            return jsonify({
                'success': False,
                'message': 'An error occurred. Please try again later.'
            }), 500
        flash('An error occurred. Please try again later.', 'danger')
        return redirect(url_for('fans.subscribe_page'))

@fans_bp.route('/fans')
def fans():
    """Main fans page - Publicly accessible"""
    try:
        # Get team settings for logo and colors
        team_settings = TeamSettings.get_settings()
        
        # Get upcoming matches (next 30 days)
        upcoming_matches = Match.query.filter(
            Match.match_date >= datetime.utcnow(),
            Match.match_date <= datetime.utcnow() + timedelta(days=30)
        ).order_by(Match.match_date.asc()).limit(5).all()
        
        # Get latest published news
        latest_news = NewsArticle.query.filter(
            NewsArticle.is_published == True
        ).order_by(NewsArticle.created_at.desc()).limit(3).all()
        
        # Format news data for template
        formatted_news = []
        for news in latest_news:
            formatted_news.append({
                'id': news.id,
                'title': news.title,
                'summary': news.summary or (news.content[:150] + '...' if len(news.content) > 150 else news.content),
                'image_url': url_for('static', filename=news.image_url) if news.image_url else None,
                'created_at': news.created_at,
                'author': news.author.username if news.author else 'Admin',
                'category': news.category or 'General'
            })
        
        # Format matches data for template
        formatted_matches = []
        for match in upcoming_matches:
            formatted_matches.append({
                'id': match.id,
                'opponent': match.opponent,
                'opponent_logo': url_for('static', filename=match.opponent_logo) if match.opponent_logo else None,
                'match_date': match.match_date,
                'venue': match.venue,
                'competition': match.competition,
                'is_home': match.is_home,
                'status': match.status
            })
        
        return render_template('fans/index.html', 
                             title=f'{team_settings.team_name} - Fan Zone',
                             team_settings=team_settings,
                             upcoming_matches=formatted_matches,
                             latest_news=formatted_news,
                             is_public=True,
                             now=datetime.utcnow())
    except Exception as e:
        current_app.logger.error(f"Error in fans route: {str(e)}")
        return render_template('fans/index.html', 
                             title='Fan Zone',
                             upcoming_matches=[],
                             latest_news=[],
                             is_public=True)

@fans_bp.route('/fans/register')
def register_redirect():
    """Redirect from old register URL to main fans page"""
    return redirect(url_for('fans.fans'))

@fans_bp.route('/fans/tickets')
def tickets():
    """Ticket purchase page - Publicly accessible"""
    try:
        # Get team settings
        team_settings = TeamSettings.get_settings()
        
        # Get upcoming matches (next 60 days)
        upcoming_matches = Match.query.filter(
            and_(
                Match.match_date >= datetime.utcnow(),
                Match.match_date <= datetime.utcnow() + timedelta(days=60)
            )
        ).order_by(Match.match_date.asc()).all()
        
        return render_template('fans/tickets.html',
                             title='Buy Tickets',
                             team_settings=team_settings,
                             upcoming_matches=upcoming_matches,
                             is_public=True)
    except Exception as e:
        current_app.logger.error(f"Error in tickets route: {str(e)}")
        return render_template('fans/tickets.html',
                             title='Buy Tickets',
                             upcoming_matches=[],
                             is_public=True)

@fans_bp.route('/fans/tickets/<int:match_id>', methods=['GET'])
def purchase_tickets(match_id):
    """Ticket purchase form for a specific match"""
    try:
        # Get team settings
        team_settings = TeamSettings.get_settings()
        
        # Get the match
        match = Match.query.get_or_404(match_id)
        
        # Check if match is in the future
        if match.match_date < datetime.utcnow():
            flash('Ticket sales for this match have ended.', 'warning')
            return redirect(url_for('fans.tickets'))
        
        return render_template('fans/purchase_ticket.html',
                             title=f'Buy Tickets - {match.opponent}',
                             team_settings=team_settings,
                             match=match,
                             is_public=True)
    except Exception as e:
        current_app.logger.error(f"Error in purchase_tickets route: {str(e)}")
        flash('An error occurred while loading the ticket page.', 'danger')
        return redirect(url_for('fans.tickets'))

@fans_bp.route('/fans/tickets/<int:match_id>/process', methods=['POST'])
@login_required
def process_payment(match_id):
    """Process ticket payment (stub implementation)"""
    try:
        # In a real application, this would integrate with a payment processor
        # For now, we'll just create a record of the purchase
        
        # Get form data
        general_qty = int(request.form.get('general_qty', 0))
        premium_qty = int(request.form.get('premium_qty', 0))
        
        if general_qty <= 0 and premium_qty <= 0:
            flash('Please select at least one ticket.', 'warning')
            return redirect(url_for('fans.purchase_tickets', match_id=match_id))
        
        # Create a ticket purchase record
        purchase = TicketPurchase(
            user_id=current_user.id,
            match_id=match_id,
            purchase_date=datetime.utcnow(),
            total_amount=(general_qty * 25.00) + (premium_qty * 50.00),
            status='completed',
            payment_reference=f"TKT-{uuid.uuid4().hex[:8].upper()}"
        )
        
        db.session.add(purchase)
        db.session.flush()  # Get the purchase ID for the tickets
        
        # Create ticket records
        tickets = []
        for _ in range(general_qty):
            ticket = Ticket(
                purchase_id=purchase.id,
                ticket_type='general',
                price=25.00,
                seat_number=f"GEN-{os.urandom(4).hex().upper()}",
                is_used=False
            )
            tickets.append(ticket)
        
        for _ in range(premium_qty):
            ticket = Ticket(
                purchase_id=purchase.id,
                ticket_type='premium',
                price=50.00,
                seat_number=f"PRM-{os.urandom(4).hex().upper()}",
                is_used=False
            )
            tickets.append(ticket)
        
        db.session.add_all(tickets)
        db.session.commit()
        
        # In a real app, you would send an email with the tickets here
        flash('Your tickets have been purchased successfully!', 'success')
        return redirect(url_for('fans.tickets'))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error processing payment: {str(e)}")
        flash('An error occurred while processing your payment. Please try again.', 'danger')
        return redirect(url_for('fans.purchase_tickets', match_id=match_id))

@fans_bp.route('/fans/benefits')
def benefits():
    """Fan benefits page - Publicly accessible"""
    # Static benefits data since we're not tracking memberships anymore
    benefits = [
        {
            'title': 'Exclusive Content',
            'icon': 'star',
            'description': 'Access to behind-the-scenes videos, player interviews, and exclusive match content.'
        },
        {
            'title': 'Match Updates',
            'icon': 'bell',
            'description': 'Get the latest match updates, team news, and player statistics.'
        },
        {
            'title': 'Team Shop',
            'icon': 'tshirt',
            'description': 'Shop official team merchandise and show your support on match days.'
        },
        {
            'title': 'Matchday Experience',
            'icon': 'trophy',
            'description': 'Learn about matchday activities, stadium information, and fan zones.'
        },
        {
            'title': 'Community',
            'icon': 'users',
            'description': 'Join our fan community and connect with fellow supporters.'
        },
        {
            'title': 'Newsletter',
            'icon': 'envelope',
            'description': 'Subscribe to our newsletter for the latest updates and special offers.'
        }
    ]
    
    return render_template('fans/benefits.html', 
                         title='Fan Benefits',
                         benefits=benefits,
                         is_public=True)

@fans_bp.route('/fans/events')
def events():
    """Upcoming fan events - Publicly accessible"""
    try:
        # Get team settings for logo and colors
        team_settings = TeamSettings.get_settings()
        
        # Get all upcoming events (matches and other events)
        now = datetime.utcnow()
        
        # Get upcoming matches (next 30 days)
        matches = Match.query.filter(
            Match.match_date >= now,
            Match.match_date <= now + timedelta(days=30)
        ).order_by(Match.match_date.asc()).all()
        
        # Get other upcoming events (training sessions marked as events)
        events = TrainingSession.query.filter(
            TrainingSession.session_date >= now,
            TrainingSession.session_date <= now + timedelta(days=30),
            TrainingSession.session_type == 'event'
        ).order_by(TrainingSession.session_date.asc()).all()
        
        # Combine and sort all events
        all_events = []
        
        # Add matches
        for match in matches:
            all_events.append({
                'type': 'match',
                'id': match.id,
                'title': f"Match: {team_settings.team_name} vs {match.opponent}",
                'description': f"{match.competition if match.competition else 'Friendly Match'}",
                'date': match.match_date,
                'time': match.match_date.time(),
                'location': match.venue,
                'is_match': True,
                'match_id': match.id,
                'opponent': match.opponent
            })
        
        # Add other events
        for event in events:
            all_events.append({
                'type': 'event',
                'id': event.id,
                'title': event.title,
                'description': event.description or 'No description available',
                'date': event.session_date,
                'time': event.session_date.time(),
                'location': event.location,
                'is_match': False
            })
        
        # Sort all events by date
        all_events.sort(key=lambda x: datetime.strptime(x['date'], '%Y-%m-%d'))
        
        # Get featured events (first 2 matches + any featured events)
        featured_events = []
        for event in all_events:
            if event.get('is_featured', False) or len(featured_events) < 3:
                featured_events.append(event)
            if len(featured_events) >= 3:
                break
        
        # Format dates for the template
        current_date = datetime.utcnow().strftime('%Y-%m-%d')
        
        return render_template('fans/events.html', 
                             title=f'{team_settings.team_name} - Events',
                             team_settings=team_settings,
                             events=all_events,
                             featured_events=featured_events,
                             now=current_date,
                             is_public=True)
    except Exception as e:
        current_app.logger.error(f"Error in events route: {str(e)}")
        return render_template('fans/events.html',
                             title='Fan Events',
                             events=[],
                             featured_events=[],
                             now=datetime.utcnow().strftime('%Y-%m-%d'),
                             is_public=True)

@fans_bp.route('/fans/community')
@login_required
def community():
    """Fan community chat page - Requires login"""
    try:
        team_settings = TeamSettings.get_settings()
        return render_template('fans/community.html', 
                             team_settings=team_settings,
                             title=f'{team_settings.team_name} - Fan Community')
    except Exception as e:
        current_app.logger.error(f"Error in community route: {str(e)}")
        flash('An error occurred while loading the community page. Please try again later.', 'danger')
        return redirect(url_for('fans.fans'))

@fans_bp.route('/fans/shop')
def shop():
    """Team shop page - Publicly accessible"""
    try:
        current_app.logger.info("Starting shop route execution")
        
        try:
            # Get team settings
            current_app.logger.info("Fetching team settings...")
            team_settings = TeamSettings.get_settings()
            if not team_settings:
                current_app.logger.error("No team settings found")
                flash('Team settings not configured. Please contact the administrator.', 'danger')
                return redirect(url_for('fans.fans'))
                
            current_app.logger.info(f"Team settings: {team_settings.team_name}")
            
            # Get all active categories with their active products
            current_app.logger.info("Fetching product categories...")
            try:
                categories = ProductCategory.query.filter_by(is_active=True).order_by(ProductCategory.name).all()
                current_app.logger.info(f"Found {len(categories)} categories")
            except Exception as e:
                current_app.logger.error(f"Error fetching categories: {str(e)}", exc_info=True)
                categories = []
            
            # Get featured products
            current_app.logger.info("Fetching featured products...")
            try:
                featured_products = Product.query.filter_by(
                    is_active=True, 
                    is_featured=True
                ).order_by(Product.name).all()
                current_app.logger.info(f"Found {len(featured_products)} featured products")
            except Exception as e:
                current_app.logger.error(f"Error fetching featured products: {str(e)}", exc_info=True)
                featured_products = []
            
            # Get all active products (for the all products section)
            current_app.logger.info("Fetching all active products...")
            try:
                all_products = Product.query.filter_by(is_active=True).order_by(Product.name).all()
                current_app.logger.info(f"Found {len(all_products)} total products")
                
                # Log product details for debugging
                for i, product in enumerate(all_products[:5], 1):
                    current_app.logger.info(f"Product {i}: {product.name} (ID: {product.id}, Category: {product.category_id})")
                    
                    # Ensure product has required attributes
                    if not hasattr(product, 'images'):
                        current_app.logger.warning(f"Product {product.id} is missing 'images' relationship")
                    
            except Exception as e:
                current_app.logger.error(f"Error fetching products: {str(e)}", exc_info=True)
                all_products = []
            
            # Prepare template context
            context = {
                'team_settings': team_settings,
                'categories': categories,
                'featured_products': featured_products,
                'all_products': all_products,
                'title': f'{team_settings.team_name} - Team Shop'
            }
            current_app.logger.info(f"Template context: {str(context)}")
            
            current_app.logger.info("Rendering shop template...")
            return render_template('fans/shop.html', **context)
            
        except Exception as e:
            current_app.logger.error(f"Error in shop route: {str(e)}", exc_info=True)
            flash('An error occurred while loading the team shop. Please try again later.', 'danger')
            return redirect(url_for('fans.fans'))
            
    except Exception as e:
        current_app.logger.error(f"Unexpected error in shop route: {str(e)}", exc_info=True)
        flash('An unexpected error occurred. Please try again later.', 'danger')
        return redirect(url_for('fans.fans'))
        
    except Exception as e:
        error_msg = f"Error in shop route: {str(e)}"
        current_app.logger.error(error_msg, exc_info=True)
        flash('An error occurred while loading the team shop. Please try again later.', 'danger')
        return redirect(url_for('fans.fans'))

@fans_bp.route('/api/chat/messages')
def get_chat_messages():
    """API endpoint to get recent chat messages"""
    try:
        messages = FanMessage.query.order_by(desc(FanMessage.created_at)).limit(50).all()
        return jsonify({
            'status': 'success',
            'messages': [{
                'id': msg.id,
                'user_id': msg.user_id,
                'username': msg.username,
                'message': msg.message,
                'avatar': url_for('static', filename=msg.avatar) if msg.avatar else url_for('static', filename='img/default-avatar.png'),
                'timestamp': msg.created_at.isoformat()
            } for msg in reversed(messages)]  # Return in chronological order
        })
    except Exception as e:
        current_app.logger.error(f"Error fetching chat messages: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to load chat messages'
        }), 500
