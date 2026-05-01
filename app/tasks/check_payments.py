# 18. app/tasks/check_payments.py
# SLIK V1.0 - Tâche planifiée : suspension automatique des salons impayés (APScheduler)

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from flask import current_app
from app import db
from app.models import Tenant

scheduler = BackgroundScheduler()

def suspendre_tenants_impayes():
    """
    Parcourt les tenants actifs et suspend ceux dont la date
    de dernier paiement dépasse la période de grâce configurée.
    """
    with scheduler.app.app_context():
        grace_days = current_app.config['SUSPENSION_GRACE_PERIOD_DAYS']
        date_limite = datetime.utcnow() - timedelta(days=grace_days)

        tenants_a_suspendre = Tenant.query.filter(
            Tenant.active == True,
            Tenant.last_payment_date < date_limite
        ).all()

        for tenant in tenants_a_suspendre:
            tenant.active = False
            current_app.logger.info(
                f"Tâche SLIK : Salon '{tenant.slug}' suspendu (dernier paiement : "
                f"{tenant.last_payment_date.strftime('%d/%m/%Y')})."
            )

        if tenants_a_suspendre:
            db.session.commit()
            current_app.logger.info(
                f"Tâche SLIK : {len(tenants_a_suspendre)} salon(s) suspendu(s) automatiquement."
            )


def init_scheduler(app):
    """Démarre le planificateur avec une vérification quotidienne."""
    scheduler.app = app
    scheduler.add_job(
        func=suspendre_tenants_impayes,
        trigger='interval',
        hours=24,
        id='check_payments'
    )
    scheduler.start()
    app.logger.info("SLIK Scheduler : vérification quotidienne des impayés activée.")