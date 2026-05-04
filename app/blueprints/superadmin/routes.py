from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user
from app.models import db, Tenant, Log, User
from app.utils.decorators import superadmin_required

superadmin_bp = Blueprint('superadmin', __name__)

@superadmin_bp.route('/dashboard')
@login_required
@superadmin_required
def dashboard():
    tenants = Tenant.query.all()
    today = datetime.utcnow()
    data = []
    for t in tenants:
        # Calcul de l'expiration : dernier paiement + 30 jours
        if t.active and t.last_payment_date:
            expire_at = t.last_payment_date + timedelta(days=30)
        else:
            expire_at = None

        if t.active:
            if t.last_payment_date and t.last_payment_date >= today - timedelta(days=30):
                voyant = 'vert'
            elif t.last_payment_date and t.last_payment_date < today - timedelta(days=30):
                voyant = 'orange'
            else:
                voyant = 'vert'
        else:
            voyant = 'rouge'

        data.append({
            'id': t.id,
            'slug': t.slug,
            'nom': t.nom,
            'ville': t.ville,
            'active': t.active,
            'voyant': voyant,
            'created_at': t.created_at.strftime('%d/%m/%Y'),
            'last_payment': t.last_payment_date.strftime('%d/%m/%Y') if t.last_payment_date else 'N/A',
            'expire_at': expire_at.strftime('%Y-%m-%dT%H:%M:%S') if expire_at else ''
        })
    return render_template('superadmin/index.html', tenants=data)

@superadmin_bp.route('/tenant/create', methods=['GET', 'POST'])
@login_required
@superadmin_required
def tenant_create():
    if request.method == 'POST':
        nom = request.form.get('nom', '').strip()
        phone = request.form.get('phone', '')
        ville = request.form.get('ville', '')
        slug = request.form.get('slug', '').strip().lower()
        adresse = request.form.get('adresse_text', '')
        if not nom or not slug:
            flash('Nom et slug obligatoires', 'error')
            return redirect(url_for('superadmin.tenant_create'))
        if Tenant.query.filter_by(slug=slug).first():
            flash('Ce slug est déjà utilisé', 'error')
            return redirect(url_for('superadmin.tenant_create'))
        tenant = Tenant(slug=slug, nom=nom, phone=phone, ville=ville, adresse_text=adresse,
                        active=True, created_at=datetime.utcnow(),
                        last_payment_date=datetime.utcnow())
        db.session.add(tenant)
        db.session.flush()
        email = f"{slug}@slik.cd"
        password = "123456"
        admin_user = User(email=email, role='tenant_admin', tenant_slug=slug, created_at=datetime.utcnow())
        admin_user.set_password(password)
        db.session.add(admin_user)
        db.session.commit()
        log = Log(tenant_slug=slug, event_type='tenant_created',
                  message=f'Tenant {nom} créé par superadmin {current_user.email}')
        db.session.add(log)
        db.session.commit()
        flash(f'Tenant {nom} créé avec succès. Login admin : {email} / mdp : {password}', 'success')
        return redirect(url_for('superadmin.dashboard'))
    return render_template('superadmin/tenant_create.html')

@superadmin_bp.route('/tenant/toggle/<int:id>', methods=['POST'])
@login_required
@superadmin_required
def tenant_toggle(id):
    tenant = Tenant.query.get_or_404(id)
    tenant.active = not tenant.active
    db.session.commit()
    msg = f'Tenant {tenant.nom} {"activé" if tenant.active else "suspendu"}'
    flash(msg, 'success')
    return redirect(url_for('superadmin.dashboard'))

@superadmin_bp.route('/tenant/extend/<int:id>', methods=['POST'])
@login_required
@superadmin_required
def tenant_extend(id):
    tenant = Tenant.query.get_or_404(id)
    tenant.last_payment_date = datetime.utcnow()
    tenant.active = True
    db.session.commit()
    flash(f'Paiement de {tenant.nom} prolongé jusqu\'au {tenant.last_payment_date.strftime("%d/%m/%Y")}', 'success')
    return redirect(url_for('superadmin.dashboard'))

@superadmin_bp.route('/logs/<int:tenant_id>')
@login_required
@superadmin_required
def tenant_logs(tenant_id):
    tenant = Tenant.query.get_or_404(tenant_id)
    logs = Log.query.filter_by(tenant_slug=tenant.slug).order_by(Log.created_at.desc()).limit(10).all()
    logs_data = [{'event': log.event_type, 'message': log.message,
                  'date': log.created_at.strftime('%d/%m/%Y %H:%M')} for log in logs]
    return jsonify(logs_data)
