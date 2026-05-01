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
    END IF;

    IF NEW.categorie = 'Coiffure Mariee' THEN
        INSERT INTO services (id, tenant_slug, categorie, nom, prix, duree, is_preset, is_vip, actif) VALUES
            (gen_random_uuid(), NEW.tenant_slug, 'Coiffure Mariee', '3 coiffures', '150$', '5h', TRUE, TRUE, TRUE),
            (gen_random_uuid(), NEW.tenant_slug, 'Coiffure Mariee', '2 coiffures', '100$', '3h', TRUE, FALSE, TRUE),
            (gen_random_uuid(), NEW.tenant_slug, 'Coiffure Mariee', '1 coiffure', '50$', '2h', TRUE, FALSE, TRUE),
            (gen_random_uuid(), NEW.tenant_slug, 'Coiffure Mariee', 'Forfait 3 coiff + 3 make-up', '180$', '6h', TRUE, TRUE, TRUE),
            (gen_random_uuid(), NEW.tenant_slug, 'Coiffure Mariee', 'Forfait VIP Complet', '400$', 'journee', TRUE, TRUE, TRUE);
    END IF;

    IF NEW.categorie = 'Barber' THEN
        INSERT INTO services (id, tenant_slug, categorie, nom, prix, duree, is_preset, actif) VALUES
            (gen_random_uuid(), NEW.tenant_slug, 'Barber', 'Coupe Classique', '5.000FC', '20min', TRUE, TRUE),
            (gen_random_uuid(), NEW.tenant_slug, 'Barber', 'Degrade Americain', '7.000FC', '30min', TRUE, TRUE),
            (gen_random_uuid(), NEW.tenant_slug, 'Barber', 'Taille Barbe', '5.000FC', '15min', TRUE, TRUE),
            (gen_random_uuid(), NEW.tenant_slug, 'Barber', 'Soin Barbe Complet', '10.000FC', '30min', TRUE, TRUE),
            (gen_random_uuid(), NEW.tenant_slug, 'Barber', 'Combo Coupe+Barbe', '10.000FC', '40min', TRUE, TRUE),
            (gen_random_uuid(), NEW.tenant_slug, 'Barber', 'Gommage Visage', '8.000FC', '20min', TRUE, TRUE);
    END IF;

    IF NEW.categorie = 'Coiffure Homme' THEN
        INSERT INTO services (id, tenant_slug, categorie, nom, prix, duree, is_preset, actif) VALUES
            (gen_random_uuid(), NEW.tenant_slug, 'Coiffure Homme', 'Coupe Homme Classique', '8.000FC', '25min', TRUE, TRUE),
            (gen_random_uuid(), NEW.tenant_slug, 'Coiffure Homme', 'Coupe Afro', '10.000FC', '30min', TRUE, TRUE),
            (gen_random_uuid(), NEW.tenant_slug, 'Coiffure Homme', 'Torsades', '10.000FC', '45min', TRUE, TRUE),
            (gen_random_uuid(), NEW.tenant_slug, 'Coiffure Homme', 'Vanilles', '12.000FC', '40min', TRUE, TRUE),
            (gen_random_uuid(), NEW.tenant_slug, 'Coiffure Homme', 'Coloration', '15.000FC', '1h', TRUE, TRUE);
    END IF;

    IF NEW.categorie = 'Make-up' THEN
        INSERT INTO services (id, tenant_slug, categorie, nom, prix, duree, is_preset, actif) VALUES
            (gen_random_uuid(), NEW.tenant_slug, 'Make-up', 'Simple', '15$', '30min', TRUE, TRUE),
            (gen_random_uuid(), NEW.tenant_slug, 'Make-up', 'Soiree', '20$', '45min', TRUE, TRUE),
            (gen_random_uuid(), NEW.tenant_slug, 'Make-up', 'Nude', '10$', '30min', TRUE, TRUE),
            (gen_random_uuid(), NEW.tenant_slug, 'Make-up', 'Mariee Essai+JourJ', '80$', '2h', TRUE, TRUE);
    END IF;

    IF NEW.categorie = 'Onglerie' THEN
        INSERT INTO services (id, tenant_slug, categorie, nom, prix, duree, is_preset, actif) VALUES
            (gen_random_uuid(), NEW.tenant_slug, 'Onglerie', 'Vernis permanent', '7.000FC', '45min', TRUE, TRUE),
            (gen_random_uuid(), NEW.tenant_slug, 'Onglerie', 'Capsule simple', '5$', '1h', TRUE, TRUE),
            (gen_random_uuid(), NEW.tenant_slug, 'Onglerie', 'Capsule+gel', '10$', '1h30', TRUE, TRUE),
            (gen_random_uuid(), NEW.tenant_slug, 'Onglerie', 'Pedicure Spa', '15$', '1h', TRUE, TRUE);
    END IF;

    IF NEW.categorie = 'Cils/Sourcils' THEN
        INSERT INTO services (id, tenant_slug, categorie, nom, prix, duree, is_preset, actif) VALUES
            (gen_random_uuid(), NEW.tenant_slug, 'Cils/Sourcils', 'Pose simple', '5$', '20min', TRUE, TRUE),
            (gen_random_uuid(), NEW.tenant_slug, 'Cils/Sourcils', 'Extensions naturel', '15$', '45min', TRUE, TRUE),
            (gen_random_uuid(), NEW.tenant_slug, 'Cils/Sourcils', 'Microshading', '30$', '1h30', TRUE, TRUE);
    END IF;

    IF NEW.categorie = 'Soins Visage' THEN
        INSERT INTO services (id, tenant_slug, categorie, nom, prix, duree, is_preset, actif) VALUES
            (gen_random_uuid(), NEW.tenant_slug, 'Soins Visage', 'Simple', '15$', '30min', TRUE, TRUE),
            (gen_random_uuid(), NEW.tenant_slug, 'Soins Visage', 'Complet', '20$', '1h', TRUE, TRUE);
    END IF;

    RETURN NEW;
END;
$BODY$ LANGUAGE plpgsql;
