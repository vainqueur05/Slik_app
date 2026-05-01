import json
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = "public.login"

def create_app():
    app = Flask(__name__, template_folder='../templates')
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    @app.route('/health')
    def health():
        return "OK" , 200

    # Filtres Jinja personnalisés
    app.jinja_env.filters['fromjson'] = lambda s: json.loads(s) if s else {}
    app.jinja_env.filters['get'] = lambda d, key, default='': d.get(key, default) if d else default

    # Blueprints
    from app.blueprints.public.routes import public_bp
    app.register_blueprint(public_bp, url_prefix='/')

    from app.blueprints.salon.routes import salon_bp
    app.register_blueprint(salon_bp, url_prefix='/salon')

    from app.blueprints.superadmin.routes import superadmin_bp
    app.register_blueprint(superadmin_bp, url_prefix='/superadmin')

   #@app.context_processor
   #def inject_globals():
       #return {
          # 'CLOUDINARY_CLOUD_NAME': app.config.get('CLOUDINARY_CLOUD_NAME', '')
       #}

    @app.context_processor
    def inject_cloudinary():
        return dict(CLOUDINARY_CLOUD_NAME=app.config.get('CLOUDINARY_CLOUD_NAME', ''))

    if not app.config.get('TESTING'):
        from app.tasks.scheduler import init_scheduler
        init_scheduler(app)

    from app import models  # noqa

    return app
