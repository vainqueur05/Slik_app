from app import create_app, db
from app.models import Tenant, SalonCategory, Service
import uuid

app = create_app()
with app.app_context():
    # Pour chaque tenant, on efface les anciens services preset puis on les recrée manuellement
    for tenant in Tenant.query.all():
        # Supprime les anciens services preset
        Service.query.filter_by(tenant_slug=tenant.slug, is_preset=True).delete()
        db.session.commit()

        # Récupère les catégories actives (elles sont déjà insérées ou vont l'être)
        # On va directement insérer les services par catégorie (sans passer par le trigger)
        categories_services = {
            'Coiffure Femme': [
                ('Pose perruque', '15$', '1h'),
                ('Tissage lace', '20$', '2h'),
                ('Tissage closure', '20$', '2h'),
                ('Brushing', '10$', '45min'),
                ('Box Braids Longues', '35$', '4h'),
                ('Fulani Braids', '40$', '5h')
            ],
            'Coiffure Mariee': [
                ('3 coiffures', '150$', '5h', True),
                ('2 coiffures', '100$', '3h', False),
                ('1 coiffure', '50$', '2h', False),
                ('Forfait 3 coiff + 3 make-up', '180$', '6h', True),
                ('Forfait VIP Complet', '400$', 'journee', True)
            ],
            'Barber': [
                ('Coupe Classique', '5.000FC', '20min'),
                ('Degrade Americain', '7.000FC', '30min'),
                ('Taille Barbe', '5.000FC', '15min'),
                ('Soin Barbe Complet', '10.000FC', '30min'),
                ('Combo Coupe+Barbe', '10.000FC', '40min'),
                ('Gommage Visage', '8.000FC', '20min')
            ],
            'Coiffure Homme': [
                ('Coupe Homme Classique', '8.000FC', '25min'),
                ('Coupe Afro', '10.000FC', '30min'),
                ('Torsades', '10.000FC', '45min'),
                ('Vanilles', '12.000FC', '40min'),
                ('Coloration', '15.000FC', '1h')
            ],
            'Make-up': [
                ('Simple', '15$', '30min'),
                ('Soiree', '20$', '45min'),
                ('Nude', '10$', '30min'),
                ('Mariee Essai+JourJ', '80$', '2h')
            ],
            'Onglerie': [
                ('Vernis permanent', '7.000FC', '45min'),
                ('Capsule simple', '5$', '1h'),
                ('Capsule+gel', '10$', '1h30'),
                ('Pedicure Spa', '15$', '1h')
            ],
            'Cils/Sourcils': [
                ('Pose simple', '5$', '20min'),
                ('Extensions naturel', '15$', '45min'),
                ('Microshading', '30$', '1h30')
            ],
            'Soins Visage': [
                ('Simple', '15$', '30min'),
                ('Complet', '20$', '1h')
            ]
        }

        for cat, services_list in categories_services.items():
            # Vérifie si la catégorie est bien activée pour le salon
            if not SalonCategory.query.filter_by(tenant_slug=tenant.slug, categorie=cat).first():
                # Si la catégorie n'existe pas, on l'ajoute (elle déclenchera le trigger, mais on l'évite en insérant d'abord)
                db.session.add(SalonCategory(tenant_slug=tenant.slug, categorie=cat))
            for svc in services_list:
                nom = svc[0]
                prix = svc[1]
                duree = svc[2]
                is_vip = svc[3] if len(svc) > 3 else False
                service = Service(
                    id=str(uuid.uuid4()),
                    tenant_slug=tenant.slug,
                    categorie=cat,
                    nom=nom,
                    prix=prix,
                    duree=duree,
                    is_preset=True,
                    active=True,
                    is_vip=is_vip,
                    ordre=0
                )
                db.session.add(service)
        db.session.commit()
        print(f"✅ Services ajoutés pour {tenant.slug}")
    print("🎉 Terminé")
