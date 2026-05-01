"""Ajout colonnes categorie, actif, is_preset, etc. à services

Revision ID: 1a2b3c4d
Revises: 0eefdb414d73
Create Date: 2026-05-01 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1a2b3c4d'
down_revision = '0eefdb414d73'
branch_labels = None
depends_on = None


def upgrade():
    # Ajout des colonnes manquantes dans services
    with op.batch_alter_table('services', schema=None) as batch_op:
        batch_op.add_column(sa.Column('categorie', sa.String(length=50), nullable=False, server_default='Autre'))
        batch_op.add_column(sa.Column('actif', sa.Boolean(), nullable=True, default=True))
        batch_op.add_column(sa.Column('is_preset', sa.Boolean(), nullable=True, default=True))
        batch_op.add_column(sa.Column('is_vip', sa.Boolean(), nullable=True, default=False))
        # Modifier le type de prix pour accepter les chaînes (ex: "15$") si ce n'est pas déjà fait
        batch_op.alter_column('prix', existing_type=sa.Float(), type_=sa.String(20), existing_nullable=True)
        batch_op.add_column(sa.Column('duree', sa.String(20), nullable=True))


def downgrade():
    with op.batch_alter_table('services', schema=None) as batch_op:
        batch_op.drop_column('duree')
        batch_op.alter_column('prix', existing_type=sa.String(20), type_=sa.Float(), existing_nullable=True)
        batch_op.drop_column('is_vip')
        batch_op.drop_column('is_preset')
        batch_op.drop_column('actif')
        batch_op.drop_column('categorie')