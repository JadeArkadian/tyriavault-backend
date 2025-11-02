################################################
# Seed Data
# This data is used to populate the database with initial values.
################################################

from app.database.models import Genders, Races, Rarities  # Ajusta la ruta según tu estructura

GENDERS_DATA = [
    Genders(id=1, name_en="Male", name_es="Masculino", name_de="Männlich", name_fr="Homme"),
    Genders(id=2, name_en="Female", name_es="Femenino", name_de="Weiblich", name_fr="Femme"),
]

RACES_DATA = [
    Races(id=1, name_en="Asura", name_es="Asura", name_de="Asura", name_fr="Asura"),
    Races(id=2, name_en="Charr", name_es="Charr", name_de="Charr", name_fr="Charr"),
    Races(id=3, name_en="Human", name_es="Humano", name_de="Mensch", name_fr="Humain"),
    Races(id=4, name_en="Norn", name_es="Norn", name_de="Norn", name_fr="Norn"),
    Races(id=5, name_en="Sylvari", name_es="Sylvari", name_de="Sylvari", name_fr="Sylvari"),
]

RARITIES_DATA = [
    Rarities(id=1, name_es="Basura", name_fr="Camelote", name_en="Junk", name_de="Schrott", color="#AAAAAA"),
    Rarities(id=2, name_es="Básico", name_fr="Basique", name_en="Basic", name_de="Einfach", color="#FFFFFF"),
    Rarities(id=3, name_es="Fino", name_fr="Raffiné", name_en="Fine", name_de="Fein", color="#62A2FF"),
    Rarities(id=4, name_es="Obra maestra", name_fr="Chef-d'œuvre", name_en="Masterwork", name_de="Meisterwerk", color="#1AFF1A"),
    Rarities(id=5, name_es="Excepcional", name_fr="Exceptionnel", name_en="Rare", name_de="Selten", color="#FFD91A"),
    Rarities(id=6, name_es="Exótico", name_fr="Exotique", name_en="Exotic", name_de="Exotisch", color="#FFAA1A"),
    Rarities(id=7, name_es="Ascendido", name_fr="Élevé", name_en="Ascended", name_de="Aufgestiegen", color="#FF1AFF"),
    Rarities(id=8, name_es="Legendario", name_fr="Légendaire", name_en="Legendary", name_de="Legendär", color="#AA1AFF"),
]
