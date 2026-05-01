from flask import url_for, current_app

def generate_seo_meta(tenant):
    """
    Génère le dictionnaire SEO complet pour un tenant (LOI 11).
    """
    title = f"{tenant.nom} - Meilleur Coiffeur {tenant.ville or 'Royal'}"
    desc = f"{tenant.nom} à {tenant.ville or 'votre ville'} - Votre Signature Royale. Services exclusifs : Dégradé Royal, Transformation Garantie. Réservez en 10 secondes."
    if len(desc) > 155:
        desc = desc[:152] + '...'

    canonical = url_for('public.index', slug=tenant.slug, _external=True)

    schema = {
        "@context": "https://schema.org",
        "@type": "HairSalon",
        "name": tenant.nom,
        "image": f"https://res.cloudinary.com/{current_app.config['CLOUDINARY_CLOUD_NAME']}/image/upload/{tenant.logo_cloudinary_id}" if tenant.logo_cloudinary_id else None,
        "address": {
            "@type": "PostalAddress",
            "addressLocality": tenant.ville,
            "streetAddress": tenant.adresse_text
        },
        "geo": {
            "@type": "GeoCoordinates",
            "latitude": tenant.lat,
            "longitude": tenant.lng
        },
        "telephone": tenant.phone,
        "url": canonical
    }

    return {
        'title': title,
        'description': desc,
        'canonical': canonical,
        'jsonld': schema
    }