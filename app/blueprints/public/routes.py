from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, abort
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, Tenant, Service, Coiffeur, Temoignage, Galerie, Booking, Log, User, Reservation
from app.utils.seo import generate_seo_meta
from app.utils.tenant import get_tenant_slug

public_bp = Blueprint('public', __name__)

@public_bp.route('/health')
def health_check():
    return jsonify({"status": "ok"}), 200

@public_bp.route('/init-db/<secret>')
def init_db(secret):
    if secret != 'mon-code-secret-123':
        return jsonify({'error': 'Accès refusé'}), 403

    from sqlalchemy import text, inspect
    insp = inspect(db.engine)

    # --- Étape 1 : ajouter les colonnes manquantes dans services ---
    if 'categorie' not in [c['name'] for c in insp.get_columns('services')]:
        db.session.execute(text("ALTER TABLE services ADD COLUMN categorie VARCHAR(50) DEFAULT 'Autre'"))
        db.session.commit()
    for col, coltype, default in [
        ('actif', 'BOOLEAN', 'TRUE'),
        ('is_preset', 'BOOLEAN', 'TRUE'),
        ('is_vip', 'BOOLEAN', 'FALSE'),
        ('duree', 'VARCHAR(20)', None),
    ]:
        if col not in [c['name'] for c in insp.get_columns('services')]:
            default_sql = f"DEFAULT {default}" if default else ''
            db.session.execute(text(f"ALTER TABLE services ADD COLUMN {col} {coltype} {default_sql}"))
    db.session.commit()

    # --- Étape 2 : recréer les deux fonctions et les triggers ---
    # Fonction insert_default_categories()
    db.session.execute(text("""
    CREATE OR REPLACE FUNCTION insert_default_categories()
    RETURNS TRIGGER AS $BODY$
    BEGIN
        INSERT INTO salon_categories (tenant_slug, categorie) VALUES
            (NEW.slug, 'Coiffure Femme'),
            (NEW.slug, 'Coiffure Mariee'),
            (NEW.slug, 'Barber'),
            (NEW.slug, 'Coiffure Homme'),
            (NEW.slug, 'Make-up'),
            (NEW.slug, 'Onglerie'),
            (NEW.slug, 'Cils/Sourcils'),
            (NEW.slug, 'Soins Visage'),
            (NEW.slug, 'Autre');
        RETURN NEW;
    END;
    $BODY$ LANGUAGE plpgsql;
    """))
    db.session.commit()

    # Trigger after_tenant_insert
    db.session.execute(text("DROP TRIGGER IF EXISTS after_tenant_insert ON tenants"))
    db.session.execute(text("""
    CREATE TRIGGER after_tenant_insert
    AFTER INSERT ON tenants
    FOR EACH ROW EXECUTE FUNCTION insert_default_categories();
    """))
    db.session.commit()

    # Fonction insert_preset_services()
    db.session.execute(text("""
    CREATE OR REPLACE FUNCTION insert_preset_services()
    RETURNS TRIGGER AS $BODY$
    BEGIN
        IF NEW.categorie = 'Coiffure Femme' THEN
            INSERT INTO services (id, tenant_slug, categorie, nom, prix, duree, is_preset, actif) VALUES
                (gen_random_uuid(), NEW.tenant_slug, 'Coiffure Femme', 'Pose perruque', '15$', '1h', TRUE, TRUE),
                (gen_random_uuid(), NEW.tenant_slug, 'Coiffure Femme', 'Tissage lace', '20$', '2h', TRUE, TRUE),
                (gen_random_uuid(), NEW.tenant_slug, 'Coiffure Femme', 'Tissage closure', '20$', '2h', TRUE, TRUE),
                (gen_random_uuid(), NEW.tenant_slug, 'Coiffure Femme', 'Brushing', '10$', '45min', TRUE, TRUE),
                (gen_random_uuid(), NEW.tenant_slug, 'Coiffure Femme', 'Box Braids Longues', '35$', '4h', TRUE, TRUE),
                (gen_random_uuid(), NEW.tenant_slug, 'Coiffure Femme', 'Fulani Braids', '40$', '5h', TRUE, TRUE);
        ELSIF NEW.categorie = 'Coiffure Mariee' THEN
            INSERT INTO services (id, tenant_slug, categorie, nom, prix, duree, is_preset, is_vip, actif) VALUES
                (gen_random_uuid(), NEW.tenant_slug, 'Coiffure Mariee', '3 coiffures', '150$', '5h', TRUE, TRUE, TRUE),
                (gen_random_uuid(), NEW.tenant_slug, 'Coiffure Mariee', '2 coiffures', '100$', '3h', TRUE, FALSE, TRUE),
                (gen_random_uuid(), NEW.tenant_slug, 'Coiffure Mariee', '1 coiffure', '50$', '2h', TRUE, FALSE, TRUE),
                (gen_random_uuid(), NEW.tenant_slug, 'Coiffure Mariee', 'Forfait 3 coiff + 3 make-up', '180$', '6h', TRUE, TRUE, TRUE),
                (gen_random_uuid(), NEW.tenant_slug, 'Coiffure Mariee', 'Forfait VIP Complet', '400$', 'journee', TRUE, TRUE, TRUE);
        ELSIF NEW.categorie = 'Barber' THEN
            INSERT INTO services (id, tenant_slug, categorie, nom, prix, duree, is_preset, actif) VALUES
                (gen_random_uuid(), NEW.tenant_slug, 'Barber', 'Coupe Classique', '5.000FC', '20min', TRUE, TRUE),
                (gen_random_uuid(), NEW.tenant_slug, 'Barber', 'Degrade Americain', '7.000FC', '30min', TRUE, TRUE),
                (gen_random_uuid(), NEW.tenant_slug, 'Barber', 'Taille Barbe', '5.000FC', '15min', TRUE, TRUE),
                (gen_random_uuid(), NEW.tenant_slug, 'Barber', 'Soin Barbe Complet', '10.000FC', '30min', TRUE, TRUE),
                (gen_random_uuid(), NEW.tenant_slug, 'Barber', 'Combo Coupe+Barbe', '10.000FC', '40min', TRUE, TRUE),
                (gen_random_uuid(), NEW.tenant_slug, 'Barber', 'Gommage Visage', '8.000FC', '20min', TRUE, TRUE);
        ELSIF NEW.categorie = 'Coiffure Homme' THEN
            INSERT INTO services (id, tenant_slug, categorie, nom, prix, duree, is_preset, actif) VALUES
                (gen_random_uuid(), NEW.tenant_slug, 'Coiffure Homme', 'Coupe Homme Classique', '8.000FC', '25min', TRUE, TRUE),
                (gen_random_uuid(), NEW.tenant_slug, 'Coiffure Homme', 'Coupe Afro', '10.000FC', '30min', TRUE, TRUE),
                (gen_random_uuid(), NEW.tenant_slug, 'Coiffure Homme', 'Torsades', '10.000FC', '45min', TRUE, TRUE),
                (gen_random_uuid(), NEW.tenant_slug, 'Coiffure Homme', 'Vanilles', '12.000FC', '40min', TRUE, TRUE),
                (gen_random_uuid(), NEW.tenant_slug, 'Coiffure Homme', 'Coloration', '15.000FC', '1h', TRUE, TRUE);
        ELSIF NEW.categorie = 'Make-up' THEN
            INSERT INTO services (id, tenant_slug, categorie, nom, prix, duree, is_preset, actif) VALUES
                (gen_random_uuid(), NEW.tenant_slug, 'Make-up', 'Simple', '15$', '30min', TRUE, TRUE),
                (gen_random_uuid(), NEW.tenant_slug, 'Make-up', 'Soiree', '20$', '45min', TRUE, TRUE),
                (gen_random_uuid(), NEW.tenant_slug, 'Make-up', 'Nude', '10$', '30min', TRUE, TRUE),
                (gen_random_uuid(), NEW.tenant_slug, 'Make-up', 'Mariee Essai+JourJ', '80$', '2h', TRUE, TRUE);
        ELSIF NEW.categorie = 'Onglerie' THEN
            INSERT INTO services (id, tenant_slug, categorie, nom, prix, duree, is_preset, actif) VALUES
                (gen_random_uuid(), NEW.tenant_slug, 'Onglerie', 'Vernis permanent', '7.000FC', '45min', TRUE, TRUE),
                (gen_random_uuid(), NEW.tenant_slug, 'Onglerie', 'Capsule simple', '5$', '1h', TRUE, TRUE),
                (gen_random_uuid(), NEW.tenant_slug, 'Onglerie', 'Capsule+gel', '10$', '1h30', TRUE, TRUE),
                (gen_random_uuid(), NEW.tenant_slug, 'Onglerie', 'Pedicure Spa', '15$', '1h', TRUE, TRUE);
        ELSIF NEW.categorie = 'Cils/Sourcils' THEN
            INSERT INTO services (id, tenant_slug, categorie, nom, prix, duree, is_preset, actif) VALUES
                (gen_random_uuid(), NEW.tenant_slug, 'Cils/Sourcils', 'Pose simple', '5$', '20min', TRUE, TRUE),
                (gen_random_uuid(), NEW.tenant_slug, 'Cils/Sourcils', 'Extensions naturel', '15$', '45min', TRUE, TRUE),
                (gen_random_uuid(), NEW.tenant_slug, 'Cils/Sourcils', 'Microshading', '30$', '1h30', TRUE, TRUE);
        ELSIF NEW.categorie = 'Soins Visage' THEN
            INSERT INTO services (id, tenant_slug, categorie, nom, prix, duree, is_preset, actif) VALUES
                (gen_random_uuid(), NEW.tenant_slug, 'Soins Visage', 'Simple', '15$', '30min', TRUE, TRUE),
                (gen_random_uuid(), NEW.tenant_slug, 'Soins Visage', 'Complet', '20$', '1h', TRUE, TRUE);
        END IF;
        RETURN NEW;
    END;
    $BODY$ LANGUAGE plpgsql;
    """))
    db.session.commit()

    # Trigger after_category_insert
    db.session.execute(text("DROP TRIGGER IF EXISTS after_category_insert ON salon_categories"))
    db.session.execute(text("""
    CREATE TRIGGER after_category_insert
    AFTER INSERT ON salon_categories
    FOR EACH ROW EXECUTE FUNCTION insert_preset_services();
    """))
    db.session.commit()

    # --- Étape 3 : peupler les catégories et services pour les salons existants ---
    from app.models import Tenant, SalonCategory, Service
    categories_list = ['Coiffure Femme', 'Coiffure Mariee', 'Barber', 'Coiffure Homme', 'Make-up', 'Onglerie', 'Cils/Sourcils', 'Soins Visage', 'Autre']
    for tenant in Tenant.query.all():
        # Ajouter les catégories manquantes (le trigger insérera les services)
        existing_cats = [c.categorie for c in SalonCategory.query.filter_by(tenant_slug=tenant.slug).all()]
        for cat in categories_list:
            if cat not in existing_cats:
                db.session.add(SalonCategory(tenant_slug=tenant.slug, categorie=cat))
    db.session.commit()

    # --- Étape 4 : superadmin ---
    from app.models import User
    if not User.query.filter_by(email='admin@slik.cd').first():
        u = User(email='admin@slik.cd', role='superadmin')
        u.set_password('00Kalema')
        db.session.add(u)
        db.session.commit()
        return jsonify({'message': 'Base prête, triggers créés, services peuplés, superadmin ajouté'}), 200
    return jsonify({'message': 'Base déjà prête, triggers et services mis à jour'}), 200
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

# ---------- UNIQUE route de réservation (POST) ----------
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

# ---------- Page de réservation (optionnelle) ----------
@public_bp.route('/<slug>/booking')
def booking_form(slug):
    tenant = Tenant.query.filter_by(slug=slug, active=True).first_or_404()
    services = Service.query.filter_by(tenant_slug=slug, active=True).order_by(Service.ordre).all()
    coiffeurs = Coiffeur.query.filter_by(tenant_slug=slug, active=True).all()
    return render_template('public/booking.html', tenant=tenant, services=services, coiffeurs=coiffeurs)

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
    return redirect(url_for('public.index', slug='login'))