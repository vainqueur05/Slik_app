from datetime import datetime, timedelta
from app import db
from app.models import Tenant, Log

def check_suspended_tenants():
    now = datetime.utcnow()
    deadline_suspend = now - timedelta(days=35)
    deadline_payment = now - timedelta(days=30)
    tenants_to_suspend = Tenant.query.filter(
        Tenant.active == True,
        Tenant.created_at <= deadline_suspend,
        Tenant.last_payment_date < Tenant.created_at + timedelta(days=30)
    ).all()
    for tenant in tenants_to_suspend:
        tenant.active = False
        log = Log(tenant_slug=tenant.slug, event_type='suspend_auto', message='Suspension automatique J+35')
        db.session.add(log)
    if tenants_to_suspend:
        db.session.commit()

def init_scheduler(app):
    from apscheduler.schedulers.background import BackgroundScheduler
    scheduler = BackgroundScheduler(timezone='Africa/Lubumbashi')
    scheduler.add_job(check_suspended_tenants, 'cron', hour=0, minute=1, id='auto_suspend')
    scheduler.start()
    app.scheduler = scheduler
