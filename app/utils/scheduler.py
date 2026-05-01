from datetime import datetime, timedelta
from app import db
from app.models import Tenant, Log

def check_suspended_tenants():
    """
    Tâche planifiée quotidienne (LOI 14).
    Suspend les tenants dont :
    - created_at + 35 jours < aujourd'hui
    - ET last_payment_date < created_at + 30 jours
    """
    now = datetime.utcnow()
    deadline_suspend = now - timedelta(days=35)
    deadline_payment = now - timedelta(days=30)  # approximation

    tenants_to_suspend = Tenant.query.filter(
        Tenant.active == True,
        Tenant.created_at <= deadline_suspend,
        Tenant.last_payment_date < Tenant.created_at + timedelta(days=30)
    ).all()

    count = 0
    for tenant in tenants_to_suspend:
        tenant.active = False
        log = Log(
            tenant_slug=tenant.slug,
            event_type='suspend_auto',
            message=f'Suspension automatique J+35. Dernier paiement : {tenant.last_payment_date.strftime("%d/%m/%Y") if tenant.last_payment_date else "N/A"}'
        )
        db.session.add(log)
        count += 1

    if count > 0:
        db.session.commit()
        print(f"[Scheduler] {count} tenant(s) suspendu(s) automatiquement.")

def init_scheduler(app):
    """Initialise APScheduler avec l'application Flask."""
    from apscheduler.schedulers.background import BackgroundScheduler
    scheduler = BackgroundScheduler(timezone='Africa/Lubumbashi')
    scheduler.add_job(
        check_suspended_tenants,
        'cron',
        hour=0,
        minute=1,
        id='auto_suspend'
    )
    scheduler.start()
    app.scheduler = scheduler