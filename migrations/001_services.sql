DROP TABLE IF EXISTS services CASCADE;
CREATE TABLE services (
    id VARCHAR(36) PRIMARY KEY,
    tenant_slug VARCHAR(50) NOT NULL REFERENCES tenants(slug) ON DELETE CASCADE,
    categorie VARCHAR(50) NOT NULL,
    nom VARCHAR(100) NOT NULL,
    prix VARCHAR(20),
    duree VARCHAR(20),
    ordre INTEGER DEFAULT 0,
    actif BOOLEAN DEFAULT FALSE,
    is_preset BOOLEAN DEFAULT TRUE,
    is_vip BOOLEAN DEFAULT FALSE,
    photo_cloudinary_id VARCHAR(200),
    photo_url VARCHAR(500),
    description_psycho TEXT,
    prix_barre FLOAT
);
CREATE INDEX idx_services_tenant ON services(tenant_slug);

DROP TABLE IF EXISTS salon_categories CASCADE;
CREATE TABLE salon_categories (
    id SERIAL PRIMARY KEY,
    tenant_slug VARCHAR(50) NOT NULL REFERENCES tenants(slug) ON DELETE CASCADE,
    categorie VARCHAR(50) NOT NULL,
    UNIQUE(tenant_slug, categorie)
);

DROP TABLE IF EXISTS reservations CASCADE;
CREATE TABLE reservations (
    id VARCHAR(36) PRIMARY KEY,
    tenant_slug VARCHAR(50) NOT NULL REFERENCES tenants(slug) ON DELETE CASCADE,
    client_nom VARCHAR(100),
    client_tel VARCHAR(20),
    service_id VARCHAR(36) REFERENCES services(id) ON DELETE SET NULL,
    date_rdv DATE,
    heure_rdv TIME,
    statut VARCHAR(20) DEFAULT 'confirmé',
    note TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE OR REPLACE FUNCTION insert_default_categories()
RETURNS TRIGGER AS $
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
$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS after_tenant_insert ON tenants;
CREATE TRIGGER after_tenant_insert
AFTER INSERT ON tenants
FOR EACH ROW
EXECUTE FUNCTION insert_default_categories();

CREATE OR REPLACE FUNCTION insert_preset_services()
RETURNS TRIGGER AS $
BEGIN
    IF NEW.categorie = 'Coiffure Femme' THEN
        INSERT INTO services (tenant_slug, categorie, nom, prix, duree, is_preset, actif) VALUES
            (NEW.tenant_slug, 'Coiffure Femme', 'Pose perruque', '15$', '1h', TRUE, TRUE),
            (NEW.tenant_slug, 'Coiffure Femme', 'Tissage lace', '20$', '2h', TRUE, TRUE),
            (NEW.tenant_slug, 'Coiffure Femme', 'Tissage closure', '20$', '2h', TRUE, TRUE),
            (NEW.tenant_slug, 'Coiffure Femme', 'Brushing', '10$', '45min', TRUE, TRUE),
            (NEW.tenant_slug, 'Coiffure Femme', 'Box Braids Longues', '35$', '4h', TRUE, TRUE),
            (NEW.tenant_slug, 'Coiffure Femme', 'Fulani Braids', '40$', '5h', TRUE, TRUE);
    END IF;
    IF NEW.categorie = 'Coiffure Mariee' THEN
        INSERT INTO services (tenant_slug, categorie, nom, prix, duree, is_preset, is_vip, actif) VALUES
            (NEW.tenant_slug, 'Coiffure Mariee', '3 coiffures', '150$', '5h', TRUE, TRUE, TRUE),
            (NEW.tenant_slug, 'Coiffure Mariee', '2 coiffures', '100$', '3h', TRUE, FALSE, TRUE),
            (NEW.tenant_slug, 'Coiffure Mariee', '1 coiffure', '50$', '2h', TRUE, FALSE, TRUE),
            (NEW.tenant_slug, 'Coiffure Mariee', 'Forfait 3 coiff + 3 make-up', '180$', '6h', TRUE, TRUE, TRUE),
            (NEW.tenant_slug, 'Coiffure Mariee', 'Forfait VIP Complet', '400$', 'journee', TRUE, TRUE, TRUE);
    END IF;
    IF NEW.categorie = 'Barber' THEN
        INSERT INTO services (tenant_slug, categorie, nom, prix, duree, is_preset, actif) VALUES
            (NEW.tenant_slug, 'Barber', 'Coupe Classique', '5.000FC', '20min', TRUE, TRUE),
            (NEW.tenant_slug, 'Barber', 'Degrade Americain', '7.000FC', '30min', TRUE, TRUE),
            (NEW.tenant_slug, 'Barber', 'Taille Barbe', '5.000FC', '15min', TRUE, TRUE),
            (NEW.tenant_slug, 'Barber', 'Soin Barbe Complet', '10.000FC', '30min', TRUE, TRUE),
            (NEW.tenant_slug, 'Barber', 'Combo Coupe+Barbe', '10.000FC', '40min', TRUE, TRUE),
            (NEW.tenant_slug, 'Barber', 'Gommage Visage', '8.000FC', '20min', TRUE, TRUE);
    END IF;
    IF NEW.categorie = 'Coiffure Homme' THEN
        INSERT INTO services (tenant_slug, categorie, nom, prix, duree, is_preset, actif) VALUES
            (NEW.tenant_slug, 'Coiffure Homme', 'Coupe Homme Classique', '8.000FC', '25min', TRUE, TRUE),
            (NEW.tenant_slug, 'Coiffure Homme', 'Coupe Afro', '10.000FC', '30min', TRUE, TRUE),
            (NEW.tenant_slug, 'Coiffure Homme', 'Torsades', '10.000FC', '45min', TRUE, TRUE),
            (NEW.tenant_slug, 'Coiffure Homme', 'Vanilles', '12.000FC', '40min', TRUE, TRUE),
            (NEW.tenant_slug, 'Coiffure Homme', 'Coloration', '15.000FC', '1h', TRUE, TRUE);
    END IF;
    IF NEW.categorie = 'Make-up' THEN
        INSERT INTO services (tenant_slug, categorie, nom, prix, duree, is_preset, actif) VALUES
            (NEW.tenant_slug, 'Make-up', 'Simple', '15$', '30min', TRUE, TRUE),
            (NEW.tenant_slug, 'Make-up', 'Soiree', '20$', '45min', TRUE, TRUE),
            (NEW.tenant_slug, 'Make-up', 'Nude', '10$', '30min', TRUE, TRUE),
            (NEW.tenant_slug, 'Make-up', 'Mariee Essai+JourJ', '80$', '2h', TRUE, TRUE);
    END IF;
    IF NEW.categorie = 'Onglerie' THEN
        INSERT INTO services (tenant_slug, categorie, nom, prix, duree, is_preset, actif) VALUES
            (NEW.tenant_slug, 'Onglerie', 'Vernis permanent', '7.000FC', '45min', TRUE, TRUE),
            (NEW.tenant_slug, 'Onglerie', 'Capsule simple', '5$', '1h', TRUE, TRUE),
            (NEW.tenant_slug, 'Onglerie', 'Capsule+gel', '10$', '1h30', TRUE, TRUE),
            (NEW.tenant_slug, 'Onglerie', 'Pedicure Spa', '15$', '1h', TRUE, TRUE);
    END IF;
    IF NEW.categorie = 'Cils/Sourcils' THEN
        INSERT INTO services (tenant_slug, categorie, nom, prix, duree, is_preset, actif) VALUES
            (NEW.tenant_slug, 'Cils/Sourcils', 'Pose simple', '5$', '20min', TRUE, TRUE),
            (NEW.tenant_slug, 'Cils/Sourcils', 'Extensions naturel', '15$', '45min', TRUE, TRUE),
            (NEW.tenant_slug, 'Cils/Sourcils', 'Microshading', '30$', '1h30', TRUE, TRUE);
    END IF;
    IF NEW.categorie = 'Soins Visage' THEN
        INSERT INTO services (tenant_slug, categorie, nom, prix, duree, is_preset, actif) VALUES
            (NEW.tenant_slug, 'Soins Visage', 'Simple', '15$', '30min', TRUE, TRUE),
            (NEW.tenant_slug, 'Soins Visage', 'Complet', '20$', '1h', TRUE, TRUE);
    END IF;
    RETURN NEW;
END;
$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS after_category_insert ON salon_categories;
CREATE TRIGGER after_category_insert
AFTER INSERT ON salon_categories
FOR EACH ROW
EXECUTE FUNCTION insert_preset_services();
