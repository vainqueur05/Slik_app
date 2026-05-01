from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, IntegerField, TextAreaField, BooleanField, HiddenField
from wtforms.validators import DataRequired, Optional, NumberRange, Length

class ServiceForm(FlaskForm):
    id = HiddenField('ID')
    nom = StringField('Nom du service', validators=[DataRequired(), Length(max=100)])
    categorie = StringField('Catégorie', validators=[DataRequired(), Length(max=50)])
    prix = StringField('Prix', validators=[Optional(), Length(max=20)])  # ex: "15$"
    duree = StringField('Durée', validators=[Optional(), Length(max=20)]) # ex: "1h"
    is_vip = BooleanField('Service VIP')
    actif = BooleanField('Actif')
    ordre = IntegerField('Ordre', validators=[Optional()], default=0)
    description_psycho = TextAreaField('Description psycho', validators=[Optional(), Length(max=500)])
    photo_cloudinary_id = HiddenField('Cloudinary ID')
    # photo_url sera gérée séparément

class CoiffeurForm(FlaskForm):
    id = HiddenField('ID')
    nom = StringField('Nom', validators=[DataRequired(), Length(max=100)])
    specialite = StringField('Spécialité', validators=[Optional(), Length(max=200)])
    instagram = StringField('Instagram', validators=[Optional(), Length(max=100)])
    annees_exp = IntegerField('Années d\'expérience', validators=[Optional(), NumberRange(min=0)], default=0)
    actif = BooleanField('Actif', default=True)
    photo_cloudinary_id = HiddenField('Cloudinary ID')

class GalerieForm(FlaskForm):
    photo_cloudinary_id = HiddenField('Cloudinary ID', validators=[DataRequired()])
    type = StringField('Type', validators=[DataRequired()], default='avant')
    legende = StringField('Légende', validators=[Optional(), Length(max=200)])