import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models import db, Tenant, Service, Coiffeur, Temoignage, Galerie, Booking, Log, User, SalonCategory, Reservation
from app.utils.cloudinary import upload_cloudinary_image
from app.utils.tenant import get_tenant_slug, tenant_required
from app.utils.decorators import admin_required
from datetime import datetime

salon_bp = Blueprint('salon', __name__, template_folder='../../../templates/salon')

@salon_bp.route('/<slug>/suspendu')
def suspendu(slug):
    tenant = Tenant.query.filter_by(slug=slug).first_or_404()
    return render_template('503_suspended.html', tenant=tenant)

@salon_bp.route('/<slug>/admin')
@login_required
@admin_required
@tenant_required
def admin(slug):
    tenant = Tenant.query.filter_by(slug=slug).first_or_404()
    counts = {
        'services': Service.query.filter_by(tenant_slug=slug).count(),
        'coiffeurs': Coiffeur.query.filter_by(tenant_slug=slug).count(),
        'bookings': Booking.query.filter_by(tenant_slug=slug).count(),
        'galerie': Galerie.query.filter_by(tenant_slug=slug).count(),
        'temoignages': Temoignage.query.filter_by(tenant_slug=slug).count(),
    }
    return render_template('admin.html', tenant=tenant, counts=counts)

# ==============================
# NOUVELLES ROUTES (Settings + Services)
# ==============================

@salon_bp.route('/<slug>/admin/settings', methods=['GET', 'POST'])
@login_required
@admin_required
@tenant_required
def admin_settings(slug):
    tenant = Tenant.query.filter_by(slug=slug).first_or_404()
    all_categories = ['Coiffure Femme', 'Coiffure Mariée', 'Barber', 'Make-up',
                      'Onglerie', 'Cils/Sourcils', 'Soins Visage', 'Autre']

    if request.method == 'POST':
        selected = request.form.getlist('categories')
        SalonCategory.query.filter_by(tenant_slug=slug).delete()
        for cat in selected:
            db.session.add(SalonCategory(tenant_slug=slug, categorie=cat))
        db.session.commit()
        flash('Paramètres sauvegardés', 'success')
        return redirect(url_for('salon.admin_settings', slug=slug))

    active_cats = [c.categorie for c in SalonCategory.query.filter_by(tenant_slug=slug).all()]
    return render_template('salon/admin_settings.html', tenant=tenant,
                           categories=all_categories, active_cats=active_cats)

@salon_bp.route('/<slug>/admin/services', methods=['GET', 'POST'])
@login_required
@admin_required
@tenant_required
def admin_services(slug):
    tenant = Tenant.query.filter_by(slug=slug).first_or_404()
    active_cats = [c.categorie for c in SalonCategory.query.filter_by(tenant_slug=slug).all()]

    if request.method == 'POST':
        # Mise à jour des prix, durées, activation
        for key, val in request.form.items():
            if key.startswith('prix_'):
                service_id = key.replace('prix_', '')
                service = Service.query.get(service_id)
                if service and service.tenant_slug == slug:
                    service.prix = val
            elif key.startswith('duree_'):
                service_id = key.replace('duree_', '')
                service = Service.query.get(service_id)
                if service and service.tenant_slug == slug:
                    service.duree = val
            elif key.startswith('actif_'):
                service_id = key.replace('actif_', '')
                service = Service.query.get(service_id)
                if service and service.tenant_slug == slug:
                    service.actif = val == 'on'
        # Sauvegarde de l'ordre
        order_data = request.form.get('ordre')
        if order_data:
            order_list = order_data.split(',')
            for idx, service_id in enumerate(order_list):
                service = Service.query.get(service_id)
                if service and service.tenant_slug == slug:
                    service.ordre = idx
        db.session.commit()
        flash('Services mis à jour', 'success')
        return redirect(url_for('salon.admin_services', slug=slug))

    # Liste des services filtrée par catégories actives
    services = Service.query.filter(
        Service.tenant_slug == slug,
        Service.categorie.in_(active_cats)
    ).order_by(Service.ordre).all()
    return render_template('admin_services.html', tenant=tenant, services=services, categories=active_cats)

@salon_bp.route('/<slug>/admin/services/create', methods=['POST'])
@login_required
@admin_required
@tenant_required
def admin_service_create(slug):
    nom = request.form.get('nom', '').strip()
    categorie = request.form.get('categorie', '')
    prix = request.form.get('prix', '')
    duree = request.form.get('duree', '')
    if not nom or not categorie:
        flash('Nom et catégorie obligatoires', 'error')
        return redirect(url_for('salon.admin_services', slug=slug))
    service = Service(
        tenant_slug=slug,
        nom=nom,
        categorie=categorie,
        prix=prix,
        duree=duree,
        is_preset=False,
        actif=True,
        ordre=Service.query.filter_by(tenant_slug=slug, categorie=categorie).count()
    )
    db.session.add(service)
    db.session.commit()
    flash('Service ajouté', 'success')
    return redirect(url_for('salon.admin_services', slug=slug))

@salon_bp.route('/<slug>/admin/services/delete/<id>', methods=['POST'])
@login_required
@admin_required
@tenant_required
def admin_service_delete(slug, id):
    service = Service.query.get_or_404(id)
    if service.tenant_slug != slug or service.is_preset:
        abort(403)
    db.session.delete(service)
    db.session.commit()
    flash('Service supprimé', 'success')
    return redirect(url_for('salon.admin_services', slug=slug))

# ==============================
# CRUD Coiffeurs (inchangé)
# ==============================
@salon_bp.route('/<slug>/admin/coiffeurs', methods=['GET', 'POST'])
@login_required
@admin_required
@tenant_required
def admin_coiffeurs(slug):
    tenant = Tenant.query.filter_by(slug=slug).first_or_404()
    if request.method == 'POST':
        coiffeur_id = request.form.get('id')
        nom = request.form.get('nom', '').strip()
        specialite = request.form.get('specialite', '')
        instagram = request.form.get('instagram', '')
        annees_exp = request.form.get('annees_exp', 0)
        cloudinary_id = request.form.get('photo_cloudinary_id', '')
        photo_url = request.form.get('photo_url', '')
        active = 'active' in request.form

        if not nom:
            flash('Nom obligatoire', 'error')
            return redirect(url_for('salon.admin_coiffeurs', slug=slug))

        if coiffeur_id:
            coiffeur = Coiffeur.query.get(int(coiffeur_id))
            if coiffeur and coiffeur.tenant_slug == slug:
                coiffeur.nom = nom
                coiffeur.specialite = specialite
                coiffeur.instagram = instagram
                coiffeur.annees_exp = int(annees_exp) if annees_exp else 0
                coiffeur.active = active
                if cloudinary_id:
                    coiffeur.photo_cloudinary_id = cloudinary_id
                    coiffeur.photo_url = photo_url or None
                db.session.commit()
                flash('Coiffeur mis à jour', 'success')
        else:
            coiffeur = Coiffeur(
                tenant_slug=slug,
                nom=nom,
                specialite=specialite,
                instagram=instagram,
                annees_exp=int(annees_exp) if annees_exp else 0,
                active=active,
                photo_cloudinary_id=cloudinary_id or None,
                photo_url=photo_url or None
            )
            db.session.add(coiffeur)
            db.session.commit()
            flash('Coiffeur ajouté', 'success')
        return redirect(url_for('salon.admin_coiffeurs', slug=slug))

    coiffeurs = Coiffeur.query.filter_by(tenant_slug=slug).all()
    return render_template('admin_coiffeurs.html', tenant=tenant, coiffeurs=coiffeurs)

@salon_bp.route('/<slug>/admin/coiffeurs/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
@tenant_required
def admin_coiffeurs_delete(slug, id):
    coiffeur = Coiffeur.query.get_or_404(id)
    if coiffeur.tenant_slug != slug:
        abort(403)
    db.session.delete(coiffeur)
    db.session.commit()
    flash('Coiffeur supprimé', 'success')
    return redirect(url_for('salon.admin_coiffeurs', slug=slug))

# ==============================
# CRUD Galerie (inchangé)
# ==============================
@salon_bp.route('/<slug>/admin/galerie', methods=['GET', 'POST'])
@login_required
@admin_required
@tenant_required
def admin_galerie(slug):
    tenant = Tenant.query.filter_by(slug=slug).first_or_404()
    if request.method == 'POST':
        cloudinary_id = request.form.get('photo_cloudinary_id')
        photo_url = request.form.get('photo_url', '')
        type_photo = request.form.get('type', 'avant')
        legende = request.form.get('legende', '')

        if not cloudinary_id:
            flash('Photo obligatoire', 'error')
            return redirect(url_for('salon.admin_galerie', slug=slug))

        gal = Galerie(
            tenant_slug=slug,
            photo_cloudinary_id=cloudinary_id,
            photo_url=photo_url,
            type=type_photo,
            legende=legende
        )
        db.session.add(gal)
        db.session.commit()
        flash('Photo ajoutée à la galerie', 'success')
        return redirect(url_for('salon.admin_galerie', slug=slug))

    galeries = Galerie.query.filter_by(tenant_slug=slug).order_by(Galerie.id.desc()).all()
    return render_template('admin_galerie.html', tenant=tenant, galeries=galeries)

@salon_bp.route('/<slug>/admin/galerie/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
@tenant_required
def admin_galerie_delete(slug, id):
    photo = Galerie.query.get_or_404(id)
    if photo.tenant_slug != slug:
        abort(403)
    db.session.delete(photo)
    db.session.commit()
    flash('Photo supprimée', 'success')
    return redirect(url_for('salon.admin_galerie', slug=slug))

# ==============================
# Témoignages (inchangé)
# ==============================
@salon_bp.route('/<slug>/admin/temoignages')
@login_required
@admin_required
@tenant_required
def admin_temoignages(slug):
    temoignages = Temoignage.query.filter_by(tenant_slug=slug).order_by(Temoignage.created_at.desc()).all()
    return render_template('admin_temoignages.html', tenant=Tenant.query.filter_by(slug=slug).first(), temoignages=temoignages)

@salon_bp.route('/<slug>/admin/temoignages/approve/<int:id>', methods=['POST'])
@login_required
@admin_required
@tenant_required
def admin_temoignages_approve(slug, id):
    tem = Temoignage.query.get_or_404(id)
    if tem.tenant_slug != slug:
        abort(403)
    tem.approved = True
    db.session.commit()
    return render_template('salon/_temoignage_row.html', avis=tem, tenant_slug=slug)

@salon_bp.route('/<slug>/admin/temoignages/photo/<int:id>', methods=['POST'])
@login_required
@admin_required
@tenant_required
def admin_temoignages_upload_photo(slug, id):
    tem = Temoignage.query.get_or_404(id)
    if tem.tenant_slug != slug:
        abort(403)
    if not tem.consentement_photo:
        return jsonify({'error': 'Le client n\'a pas donné son consentement'}), 400

    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'Fichier manquant'}), 400

    if file.content_type not in ['image/jpeg', 'image/png']:
        return jsonify({'error': 'Format image requis'}), 400

    try:
        cloudinary_id = upload_cloudinary_image(file)
        tem.photo_cloudinary_id = cloudinary_id
        tem.approved = True
        db.session.commit()
        return jsonify({'status': 'ok', 'cloudinary_id': cloudinary_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@salon_bp.route('/<slug>/admin/temoignages/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
@tenant_required
def admin_temoignages_delete(slug, id):
    tem = Temoignage.query.get_or_404(id)
    if tem.tenant_slug != slug:
        abort(403)
    db.session.delete(tem)
    db.session.commit()
    flash('Témoignage supprimé', 'success')
    return redirect(url_for('salon.admin_temoignages', slug=slug))

# ==============================
# Thème, Map, Bookings, Logo/Video/Cover (inchangés)
# ==============================
@salon_bp.route('/<slug>/admin/theme', methods=['GET', 'POST'])
@login_required
@admin_required
@tenant_required
def admin_theme(slug):
    tenant = Tenant.query.filter_by(slug=slug).first_or_404()
    if request.method == 'POST':
        import json
        theme = {
            'primary': request.form.get('primary', '#000000'),
            'secondary': request.form.get('secondary', '#D4AF37'),
            'font': request.form.get('font', 'Montserrat'),
            'hero_text': request.form.get('hero_text', tenant.nom),
            'cta_color': request.form.get('cta_color', '#DC2626')
        }
        tenant.theme_json = json.dumps(theme)
        db.session.commit()
        flash('Thème mis à jour', 'success')
        return redirect(url_for('salon.admin_theme', slug=slug))
    return render_template('admin_theme.html', tenant=tenant)

@salon_bp.route('/<slug>/admin/map', methods=['GET'])
@login_required
@admin_required
@tenant_required
def admin_map(slug):
    tenant = Tenant.query.filter_by(slug=slug).first_or_404()
    return render_template('admin_map.html', tenant=tenant)

@salon_bp.route('/<slug>/admin/map', methods=['POST'])
@login_required
@admin_required
@tenant_required
def admin_map_update(slug):
    tenant = Tenant.query.filter_by(slug=slug).first_or_404()
    lat = request.form.get('lat')
    lng = request.form.get('lng')
    if lat and lng:
        tenant.lat = float(lat)
        tenant.lng = float(lng)
        db.session.commit()
        return jsonify({'status': 'ok'})
    return jsonify({'error': 'Coordonnées manquantes'}), 400


@salon_bp.route('/<slug>/admin/update-logo', methods=['POST'])
@login_required
@admin_required
@tenant_required
def update_logo(slug):
    tenant = Tenant.query.filter_by(slug=slug).first_or_404()
    cloudinary_id = request.form.get('photo_cloudinary_id', '').strip()
    logo_url = request.form.get('logo_url', '').strip()
    if cloudinary_id:
        tenant.logo_cloudinary_id = cloudinary_id
        tenant.logo_url = logo_url or None
        db.session.commit()
        return jsonify({'status': 'ok'})
    return jsonify({'error': 'ID manquant'}), 400

@salon_bp.route('/<slug>/admin/update-video', methods=['POST'])
@login_required
@admin_required
@tenant_required
def update_video(slug):
    tenant = Tenant.query.filter_by(slug=slug).first_or_404()
    cloudinary_id = request.form.get('photo_cloudinary_id', '').strip()
    video_url = request.form.get('video_url', '').strip()
    if cloudinary_id:
        tenant.video_hero_cloudinary_id = cloudinary_id
        tenant.video_url = video_url or None
        db.session.commit()
        return jsonify({'status': 'ok'})
    return jsonify({'error': 'ID manquant'}), 400

@salon_bp.route('/<slug>/admin/update-cover', methods=['POST'])
@login_required
@admin_required
@tenant_required
def update_cover(slug):
    tenant = Tenant.query.filter_by(slug=slug).first_or_404()
    cloudinary_id = request.form.get('photo_cloudinary_id', '').strip()
    cover_url = request.form.get('cover_url', '').strip()
    if cloudinary_id:
        tenant.cover_cloudinary_id = cloudinary_id
        tenant.cover_url = cover_url or None
        db.session.commit()
        return jsonify({'status': 'ok'})
    return jsonify({'error': 'ID manquant'}), 400


@salon_bp.route('/<slug>/admin/reservations')
@login_required
@admin_required
@tenant_required
def admin_reservations(slug):
    tenant = Tenant.query.filter_by(slug=slug).first_or_404()
    date_str = request.args.get('date', '')
    if date_str:
        try:
            filter_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            reservations = Reservation.query.filter_by(tenant_slug=slug, date_rdv=filter_date).order_by(Reservation.heure_rdv.asc()).all()
        except ValueError:
            reservations = []
    else:
        reservations = Reservation.query.filter_by(tenant_slug=slug).order_by(Reservation.date_rdv.desc(), Reservation.heure_rdv.asc()).all()
    return render_template('salon/admin_reservations.html', tenant=tenant, reservations=reservations, date_str=date_str)

def admin_reservation_confirm(slug, id):
    reservation = Reservation.query.get_or_404(id)
    if reservation.tenant_slug != slug:
        abort(403)
    reservation.statut = 'confirmé'
    db.session.commit()
    flash('Réservation confirmée', 'success')
    return redirect(url_for('salon.admin_reservations', slug=slug))

@salon_bp.route('/<slug>/admin/services/update-photo', methods=['POST'])
@login_required
@admin_required
@tenant_required
def admin_service_update_photo(slug):
    service_id = request.form.get('service_id')
    photo_url = request.form.get('photo_url')
    photo_cloudinary_id = request.form.get('photo_cloudinary_id')
    service = Service.query.get(service_id)
    if service and service.tenant_slug == slug:
        service.photo_url = photo_url
        service.photo_cloudinary_id = photo_cloudinary_id
        db.session.commit()
        return jsonify({'status': 'ok'})
    return jsonify({'error': 'Service non trouvé'}), 404

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from io import BytesIO
from flask import send_file

@salon_bp.route('/<slug>/admin/reservations/export.pdf')
@login_required
@admin_required
@tenant_required
def admin_reservations_export_pdf(slug):
    tenant = Tenant.query.filter_by(slug=slug).first_or_404()
    date_str = request.args.get('date', datetime.utcnow().strftime('%Y-%m-%d'))
    try:
        filter_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return "Date invalide", 400

    reservations = Reservation.query.filter_by(
        tenant_slug=slug, date_rdv=filter_date
    ).order_by(Reservation.heure_rdv.asc()).all()

    # Génération du PDF en mémoire
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []

    styles = getSampleStyleSheet()
    style_title = styles['Title']
    style_normal = styles['Normal']

    # Titre
    title = Paragraph(f"PLANNING DU {filter_date.strftime('%d/%m/%Y')}", style_title)
    elements.append(title)
    elements.append(Spacer(1, 12))

    # Logo (si présent)
    if tenant.logo_url:
        # On peut insérer une image, mais pour simplifier on met juste le nom du salon
        pass

    elements.append(Paragraph(f"<b>{tenant.nom}</b> - {tenant.ville}", style_normal))
    elements.append(Spacer(1, 12))

    # Tableau des réservations
    data = [['Heure', 'Client', 'Téléphone', 'Service', 'Check']]
    for r in reservations:
        data.append([
            r.heure_rdv.strftime('%H:%M') if r.heure_rdv else '-',
            r.client_nom,
            r.client_tel,
            r.service.nom if r.service else '-',
            '☐'  # case à cocher vide
        ])

    table = Table(data, colWidths=[50, 100, 100, 150, 30])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#D4AF37')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("Généré par SLIK - slik.cd", style_normal))

    doc.build(elements)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"planning-{slug}-{date_str}.pdf",
        mimetype='application/pdf'
    )