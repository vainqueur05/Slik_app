from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, abort
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, Tenant, Service, Coiffeur, Temoignage, Galerie, Booking, Log, User, Reservation
from app.utils.seo import generate_seo_meta
from app.utils.tenant import get_tenant_slug

public_bp = Blueprint('public', __name__)

@public_bp.route('/<slug>')
def index(slug):
    tenant = Tenant.query.filter_by(slug=slug).first_or_404()
    if not tenant.active:
        return redirect(url_for('salon.suspendu', slug=slug))
    services = Service.query.filter_by(tenant_slug=slug, active=True).order_by(Service.ordre).all()
    coiffeurs = Coiffeur.query.filter_by(tenant_slug=slug, active=True).all()
    temoignages = Temoignage.query.filter_by(tenant_slug=slug, approved=True).limit(6).all()
    galeries = Galerie.query.filter_by(tenant_slug=slug).order_by(Galerie.id.desc()).limit(12).all()
    seo = generate_seo_meta(tenant)
    nb_creneaux = Booking.query.filter_by(tenant_slug=slug, status='en_attente').count()
    nb_creneaux = max(3 - nb_creneaux, 0)
    return render_template('salon/index.html', tenant=tenant, services=services, coiffeurs=coiffeurs, temoignages=temoignages, galeries=galeries, seo=seo, nb_creneaux=nb_creneaux)

@public_bp.route('/<slug>/temoignage/add', methods=['POST'])
def add_temoignage(slug):
    tenant = Tenant.query.filter_by(slug=slug, active=True).first_or_404()
    client_nom = request.form.get('client_nom', '').strip()
    texte = request.form.get('texte', '').strip()
    note_str = request.form.get('note', '5')
    consentement = 'consentement_photo' in request.form
    if not client_nom or not texte:
        return "<div class='text-red-400'>Nom et texte obligatoires.</div>", 400
    try:
        note = int(note_str)
        note = max(1, min(5, note))
    except:
        note = 5
    tem = Temoignage(tenant_slug=slug, client_nom=client_nom, texte=texte, note=note, consentement_photo=consentement, approved=False)
    db.session.add(tem)
    db.session.commit()
    log = Log(tenant_slug=slug, event_type='temoignage_add', message=f'{client_nom} a laissé un avis')
    db.session.add(log)
    db.session.commit()
    return "<div class='bg-green-700 text-white px-4 py-2 rounded shadow-lg'>Merci ! Votre avis est en attente de validation.</div>"

@public_bp.route('/<slug>/booking')
def booking_form(slug):
    tenant = Tenant.query.filter_by(slug=slug, active=True).first_or_404()
    services = Service.query.filter_by(tenant_slug=slug, active=True).order_by(Service.ordre).all()
    coiffeurs = Coiffeur.query.filter_by(tenant_slug=slug, active=True).all()
    return render_template('public/booking.html', tenant=tenant, services=services, coiffeurs=coiffeurs)

@public_bp.route('/<slug>/booking', methods=['POST'])
def submit_booking(slug):
    tenant = Tenant.query.filter_by(slug=slug, active=True).first_or_404()
    client_nom = request.form.get('client_nom', '').strip()
    client_phone = request.form.get('client_phone', '').strip()
    service_id = request.form.get('service_id')
    date_rdv_str = request.form.get('date_rdv', '')
    heure_rdv_str = request.form.get('heure_rdv', '')

    if not client_nom or not client_phone or not date_rdv_str or not heure_rdv_str:
        return "<div class='text-red-400'>Tous les champs sont obligatoires.</div>", 400

    try:
        date_rdv = datetime.strptime(date_rdv_str, '%Y-%m-%d').date()
        heure_rdv = datetime.strptime(heure_rdv_str, '%H:%M').time()
    except ValueError:
        return "<div class='text-red-400'>Date ou heure invalide.</div>", 400

    reservation = Reservation(
        tenant_slug=slug,
        client_nom=client_nom,
        client_tel=client_phone,
        service_id=service_id,
        date_rdv=date_rdv,
        heure_rdv=heure_rdv,
        statut='en_attente'
    )
    db.session.add(reservation)
    db.session.commit()
    return "<div class='bg-green-700 text-white px-4 py-2 rounded'>Réservation enregistrée. Le salon vous contactera.</div>"

@public_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'superadmin':
            return redirect(url_for('superadmin.dashboard'))
        else:
            return redirect(url_for('salon.admin', slug=current_user.tenant_slug))
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Connexion réussie', 'success')
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            if user.role == 'superadmin':
                return redirect(url_for('superadmin.dashboard'))
            else:
                return redirect(url_for('salon.admin', slug=user.tenant_slug))
        else:
            flash('Email ou mot de passe incorrect', 'error')
    return render_template('public/login.html')

@public_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('public.login'))

@public_bp.route('/health')
def health():
    return jsonify({'status': 'ok'}), 200

@public_bp.route('/init-db/<secret>')
def init_db(secret):
    if secret != 'mon-code-secret-123':
        return jsonify({'error': 'Accès refusé'}), 403

    from sqlalchemy import text

    try:
        db.session.rollback()
        
        # Suppression de toutes les tables existantes
        db.session.execute(text("DROP TABLE IF EXISTS reservations CASCADE"))
        db.session.execute(text("DROP TABLE IF EXISTS salon_categories CASCADE"))
        db.session.execute(text("DROP TABLE IF EXISTS bookings CASCADE"))
        db.session.execute(text("DROP TABLE IF EXISTS galerie CASCADE"))
        db.session.execute(text("DROP TABLE IF EXISTS logs CASCADE"))
        db.session.execute(text("DROP TABLE IF EXISTS temoignages CASCADE"))
        db.session.execute(text("DROP TABLE IF EXISTS coiffeurs CASCADE"))
        db.session.execute(text("DROP TABLE IF EXISTS services CASCADE"))
        db.session.execute(text("DROP TABLE IF EXISTS users CASCADE"))
        db.session.execute(text("DROP TABLE IF EXISTS tenants CASCADE"))
        db.session.commit()
        
        # Création de TOUTES les tables avec TOUTES les colonnes
        db.session.execute(text("""
        -- Tenants
        CREATE TABLE tenants (
            id SERIAL PRIMARY KEY,
            slug VARCHAR(50) UNIQUE NOT NULL,
            nom VARCHAR(100) NOT NULL,
            phone VARCHAR(20),
            ville VARCHAR(100),
            adresse_text TEXT,
            lat FLOAT,
            lng FLOAT,
            logo_cloudinary_id VARCHAR(200),
            logo_url VARCHAR(500),
            video_hero_cloudinary_id VARCHAR(200),
            video_url VARCHAR(500),
            cover_cloudinary_id VARCHAR(200),
            cover_url VARCHAR(500),
            theme_json TEXT DEFAULT '{}',
            active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT NOW(),
            last_payment_date TIMESTAMP DEFAULT NOW()
        );

        -- Users
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(120) UNIQUE NOT NULL,
            password_hash VARCHAR(256) NOT NULL,
            role VARCHAR(20) DEFAULT 'tenant_admin',
            tenant_slug VARCHAR(50) REFERENCES tenants(slug),
            created_at TIMESTAMP DEFAULT NOW()
        );

        -- Services
        CREATE TABLE services (
            id VARCHAR(36) PRIMARY KEY,
            tenant_slug VARCHAR(50) REFERENCES tenants(slug),
            categorie VARCHAR(50) DEFAULT 'Autre',
            nom VARCHAR(100) NOT NULL,
            prix VARCHAR(20),
            duree VARCHAR(20),
            ordre INTEGER DEFAULT 0,
            active BOOLEAN DEFAULT FALSE,
            is_preset BOOLEAN DEFAULT TRUE,
            is_vip BOOLEAN DEFAULT FALSE,
            photo_cloudinary_id VARCHAR(200),
            photo_url VARCHAR(500),
            description_psycho TEXT,
            prix_barre FLOAT
        );

        -- Coiffeurs
        CREATE TABLE coiffeurs (
            id SERIAL PRIMARY KEY,
            tenant_slug VARCHAR(50) REFERENCES tenants(slug),
            nom VARCHAR(100) NOT NULL,
            photo_cloudinary_id VARCHAR(200),
            photo_url VARCHAR(500),
            specialite VARCHAR(200),
            instagram VARCHAR(100),
            annees_exp INTEGER,
            active BOOLEAN DEFAULT TRUE
        );

        -- Bookings (avec acompte_tx_id)
        CREATE TABLE bookings (
            id SERIAL PRIMARY KEY,
            tenant_slug VARCHAR(50) REFERENCES tenants(slug),
            client_nom VARCHAR(100) NOT NULL,
            client_phone VARCHAR(20),
            service_id VARCHAR(36) REFERENCES services(id),
            coiffeur_id INTEGER REFERENCES coiffeurs(id),
            start_time TIMESTAMP,
            status VARCHAR(20) DEFAULT 'en_attente',
            acompte_tx_id VARCHAR(200)
        );

        -- Temoignages
        CREATE TABLE temoignages (
            id SERIAL PRIMARY KEY,
            tenant_slug VARCHAR(50) REFERENCES tenants(slug),
            client_nom VARCHAR(100),
            texte TEXT,
            note INTEGER,
            photo_cloudinary_id VARCHAR(200),
            photo_url VARCHAR(500),
            consentement_photo BOOLEAN DEFAULT FALSE,
            approved BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT NOW()
        );

        -- Galerie
        CREATE TABLE galerie (
            id SERIAL PRIMARY KEY,
            tenant_slug VARCHAR(50) REFERENCES tenants(slug),
            photo_cloudinary_id VARCHAR(200) NOT NULL,
            photo_url VARCHAR(500) NOT NULL,
            type VARCHAR(20) DEFAULT 'avant',
            legende VARCHAR(200)
        );

        -- Logs
        CREATE TABLE logs (
            id SERIAL PRIMARY KEY,
            tenant_slug VARCHAR(50) REFERENCES tenants(slug),
            event_type VARCHAR(50),
            message TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        );

        -- Salon Categories
        CREATE TABLE salon_categories (
            id SERIAL PRIMARY KEY,
            tenant_slug VARCHAR(50) REFERENCES tenants(slug),
            categorie VARCHAR(50) NOT NULL,
            UNIQUE(tenant_slug, categorie)
        );

        -- Reservations
        CREATE TABLE reservations (
            id VARCHAR(36) PRIMARY KEY,
            tenant_slug VARCHAR(50) REFERENCES tenants(slug),
            client_nom VARCHAR(100),
            client_tel VARCHAR(20),
            service_id VARCHAR(36) REFERENCES services(id),
            date_rdv DATE,
            heure_rdv TIME,
            statut VARCHAR(20) DEFAULT 'confirmé',
            note TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        );
        """))
        db.session.commit()
        
        # Créer le superadmin
        from app.models import User
        u = User(email='admin@slik.cd', role='superadmin')
        u.set_password('00Kalema')
        db.session.add(u)
        db.session.commit()
        
        return jsonify({'message': 'Base de données complète créée avec succès. Superadmin ajouté.'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500