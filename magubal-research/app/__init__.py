"""
Magubal Research Platform - Flask App Factory
"""

from flask import Flask
from flask_cors import CORS


def create_app(config_class=None):
    """Flask App Factory Pattern"""
    app = Flask(__name__, 
                static_folder='../static',
                template_folder='../templates')
    
    # Configuration
    if config_class:
        app.config.from_object(config_class)
    else:
        from .config import Config
        app.config.from_object(Config)
    
    # Enable CORS
    CORS(app)
    
    # Initialize database
    from .models import init_db
    init_db(app.config['DATABASE_PATH'])
    
    # Register Blueprints
    from .api.stock import stock_bp
    from .api.news import news_bp
    from .api.flywheel import flywheel_bp
    
    app.register_blueprint(stock_bp, url_prefix='/api')
    app.register_blueprint(news_bp, url_prefix='/api')
    app.register_blueprint(flywheel_bp, url_prefix='/api')
    
    # Main route
    @app.route('/')
    def index():
        from flask import render_template
        return render_template('index.html')
    
    @app.route('/api/health')
    def health():
        from flask import jsonify
        from datetime import datetime
        return jsonify({
            'status': 'ok',
            'platform': 'Magubal Research',
            'timestamp': datetime.now().isoformat()
        })
    
    return app
