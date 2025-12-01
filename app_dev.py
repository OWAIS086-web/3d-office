from flask import Flask
from app import db, migrate, login_manager
from config_dev import DevelopmentConfig
import os

def create_dev_app():
    """Create development app with lightweight configuration"""
    app = Flask(__name__)
    app.config.from_object(DevelopmentConfig)
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'auth_dev.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # User loader function
    @login_manager.user_loader
    def load_user(user_id):
        from models.user import User
        return User.query.get(int(user_id))
    
    # Register blueprints - use development auth controller
    from controllers.auth_controller_dev import auth_dev_bp
    from controllers.dashboard_controller import dashboard_bp
    from controllers.admin_controller import admin_bp
    from controllers.api_controller import api_bp
    
    app.register_blueprint(auth_dev_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp)
    
    # Root route
    @app.route('/')
    def index():
        from flask import render_template, redirect, url_for
        from flask_login import current_user
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.index'))
        else:
            return render_template('index.html')
    
    # Create tables
    with app.app_context():
        # Import models inside app context
        from models.user import User
        from models.face_encoding import FaceEncoding
        from models.log import Log
        from models.notification import Notification
        from models.message import Message
        from models.group import Group
        
        db.create_all()
        
        # Create default admin user if none exists
        admin_user = User.query.filter_by(is_admin=True).first()
        if not admin_user:
            admin = User(
                username='admin',
                email='admin@example.com',
                is_admin=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            
            # Create test user
            test_user = User(
                username='testuser',
                email='test@example.com',
                is_admin=False
            )
            test_user.set_password('test123')
            db.session.add(test_user)
            
            db.session.commit()
            print("✅ Default users created:")
            print("   Admin: admin / admin123")
            print("   User: testuser / test123")
    
    return app

if __name__ == '__main__':
    print("🚀 Starting Development Server (Face Recognition Disabled)")
    print("=" * 60)
    print("⚡ Fast startup mode - no ML model loading")
    print("🔓 Face recognition bypassed for quick testing")
    print("👤 Default users available:")
    print("   Admin: admin / admin123")
    print("   User: testuser / test123")
    print("=" * 60)
    
    app = create_dev_app()
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)