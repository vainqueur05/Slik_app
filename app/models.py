from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager
import uuid

class Tenant(db.Model):
    __tablename__ = 'tenants'
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(50), unique=True, nullable=False, index=True)
    nom = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    ville = db.Column(db.String(100))
    adresse_text = db.Column(db.Text)
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    logo_cloudinary_id = db.Column(db.String(200))
    logo_url = db.Column(db.String(500))
    video_hero_cloudinary_id = db.Column(db.String(200))
    video_url = db.Column(db.String(500))
    cover_cloudinary_id = db.Column(db.String(200))
    cover_url = db.Column(db.String(500))
    theme_json = db.Column(db.Text, default='{}')
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_payment_date = db.Column(db.DateTime, default=datetime.utcnow)

    users = db.relationship('User', backref='tenant', lazy=True)
    services = db.relationship('Service', backref='tenant', lazy=True)
    coiffeurs = db.relationship('Coiffeur', backref='tenant', lazy=True)
    bookings = db.relationship('Booking', backref='tenant', lazy=True)
    temoignages = db.relationship('Temoignage', backref='tenant', lazy=True)
    logs = db.relationship('Log', backref='tenant', lazy=True)
    galeries = db.relationship('Galerie', backref='tenant', lazy=True)
    categories = db.relationship('SalonCategory', backref='tenant', lazy=True)
    reservations = db.relationship('Reservation', backref='tenant', lazy=True)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='tenant_admin')
    tenant_slug = db.Column(db.String(50), db.ForeignKey('tenants.slug'), nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Nouveau modÃ¨le Service (remplace l'ancien)
class Service(db.Model):
    __tablename__ = 'services'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_slug = db.Column(db.String(50), db.ForeignKey('tenants.slug'), nullable=False, index=True)
    categorie = db.Column(db.String(50), nullable=False)
    nom = db.Column(db.String(100), nullable=False)
    prix = db.Column(db.String(20))
    duree = db.Column(db.String(20))
    ordre = db.Column(db.Integer, default=0)
    active = db.Column(db.Boolean, default=False)          # â† colonne actif
    is_preset = db.Column(db.Boolean, default=True)
    is_vip = db.Column(db.Boolean, default=False)
    photo_cloudinary_id = db.Column(db.String(200))
    photo_url = db.Column(db.String(500))
    description_psycho = db.Column(db.Text)
    prix_barre = db.Column(db.Float)
    bookings = db.relationship('Booking', backref='service', lazy=True)
    reservations = db.relationship('Reservation', backref='service', lazy=True)

class Coiffeur(db.Model):
    __tablename__ = 'coiffeurs'
    id = db.Column(db.Integer, primary_key=True)
    tenant_slug = db.Column(db.String(50), db.ForeignKey('tenants.slug'), nullable=False, index=True)
    nom = db.Column(db.String(100), nullable=False)
    photo_cloudinary_id = db.Column(db.String(200))
    photo_url = db.Column(db.String(500))
    specialite = db.Column(db.String(200))
    instagram = db.Column(db.String(100))
    annees_exp = db.Column(db.Integer)
    active = db.Column(db.Boolean, default=True)
    bookings = db.relationship('Booking', backref='coiffeur', lazy=True)

class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)
    tenant_slug = db.Column(db.String(50), db.ForeignKey('tenants.slug'), nullable=False, index=True)
    client_nom = db.Column(db.String(100), nullable=False)
    client_phone = db.Column(db.String(20))
    service_id = db.Column(db.String(36), db.ForeignKey('services.id'))  # adaptÃ© Ã  la nouvelle table
    coiffeur_id = db.Column(db.Integer, db.ForeignKey('coiffeurs.id'))
    start_time = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='en_attente')
    acompte_tx_id = db.Column(db.String(200))

class Temoignage(db.Model):
    __tablename__ = 'temoignages'
    id = db.Column(db.Integer, primary_key=True)
    tenant_slug = db.Column(db.String(50), db.ForeignKey('tenants.slug'), nullable=False, index=True)
    client_nom = db.Column(db.String(100))
    texte = db.Column(db.Text)
    note = db.Column(db.Integer)
    photo_cloudinary_id = db.Column(db.String(200))
    photo_url = db.Column(db.String(500))
    consentement_photo = db.Column(db.Boolean, default=False)
    approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Log(db.Model):
    __tablename__ = 'logs'
    id = db.Column(db.Integer, primary_key=True)
    tenant_slug = db.Column(db.String(50), db.ForeignKey('tenants.slug'), nullable=False, index=True)
    event_type = db.Column(db.String(50))
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Galerie(db.Model):
    __tablename__ = 'galerie'
    id = db.Column(db.Integer, primary_key=True)
    tenant_slug = db.Column(db.String(50), db.ForeignKey('tenants.slug'), nullable=False, index=True)
    photo_cloudinary_id = db.Column(db.String(200), nullable=False)
    photo_url = db.Column(db.String(500), nullable=False)
    type = db.Column(db.String(20), default='avant')
    legende = db.Column(db.String(200))

class SalonCategory(db.Model):
    __tablename__ = 'salon_categories'
    id = db.Column(db.Integer, primary_key=True)
    tenant_slug = db.Column(db.String(50), db.ForeignKey('tenants.slug'), nullable=False, index=True)
    categorie = db.Column(db.String(50), nullable=False)
    __table_args__ = (db.UniqueConstraint('tenant_slug', 'categorie', name='unique_salon_category'),)

class Reservation(db.Model):
    __tablename__ = 'reservations'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_slug = db.Column(db.String(50), db.ForeignKey('tenants.slug'), nullable=False, index=True)
    client_nom = db.Column(db.String(100))
    client_tel = db.Column(db.String(20))
    service_id = db.Column(db.String(36), db.ForeignKey('services.id'))
    date_rdv = db.Column(db.Date)
    heure_rdv = db.Column(db.Time)
    statut = db.Column(db.String(20), default='confirmÃ©')
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
