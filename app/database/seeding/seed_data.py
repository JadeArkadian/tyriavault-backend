################################################
# Seed Data
# This data is used to populate the database with initial values.
################################################

from app.database.models import Genders, Races, Rarities, ItemTypes  # Adjust the path according to your structure

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

ITEM_TYPES_DATA = [
    ItemTypes(id=0, name_en="Unknown", name_es="Desconocido", name_de="Unbekannt", name_fr="Inconnu"),
    ItemTypes(id=1, name_en="Armor", name_es="Armadura", name_de="Rüstung", name_fr="Armure"),
    ItemTypes(id=2, name_en="Back", name_es="Mochila", name_de="Rücken", name_fr="Dos"),
    ItemTypes(id=3, name_en="Bag", name_es="Bolsa", name_de="Beutel", name_fr="Sac"),
    ItemTypes(id=4, name_en="Consumable", name_es="Consumible", name_de="Verbrauchsgegenstand", name_fr="Consommable"),
    ItemTypes(id=5, name_en="Container", name_es="Contenedor", name_de="Behälter", name_fr="Conteneur"),
    ItemTypes(id=6, name_en="Crafting Material", name_es="Material de fabricación", name_de="Handwerksmaterial",
              name_fr="Matériau d'artisanat"),
    ItemTypes(id=7, name_en="Gathering", name_es="Recolección", name_de="Sammeln", name_fr="Récolte"),
    ItemTypes(id=8, name_en="Gizmo", name_es="Artilugio", name_de="Gadget", name_fr="Gadget"),
    ItemTypes(id=9, name_en="Jade Tech Module", name_es="Módulo de tecnología de jade", name_de="Jade-Technikmodul",
              name_fr="Module technologique en jade"),
    ItemTypes(id=10, name_en="Key", name_es="Llave", name_de="Schlüssel", name_fr="Clé"),
    ItemTypes(id=11, name_en="Mini Pet", name_es="Mini mascota", name_de="Mini-Pet", name_fr="Mini animal de compagnie"),
    ItemTypes(id=12, name_en="Power Core", name_es="Núcleo de energía", name_de="Energiekern", name_fr="Noyau d'énergie"),
    ItemTypes(id=13, name_en="Relic", name_es="Reliquia", name_de="Relikt", name_fr="Relique"),
    ItemTypes(id=14, name_en="Tool", name_es="Herramienta", name_de="Werkzeug", name_fr="Outil"),
    ItemTypes(id=15, name_en="Trait", name_es="Rasgo", name_de="Eigenschaft", name_fr="Trait"),
    ItemTypes(id=16, name_en="Trinket", name_es="Baratija", name_de="Schmuckstück", name_fr="Bijou"),
    ItemTypes(id=17, name_en="Trophy", name_es="Trofeo", name_de="Trophäe", name_fr="Trophée"),
    ItemTypes(id=18, name_en="Upgrade Component", name_es="Componente de mejora", name_de="Aufwertungskomponente",
              name_fr="Composant de mise à niveau"),
    ItemTypes(id=19, name_en="Weapon", name_es="Arma", name_de="Waffe", name_fr="Arme")
]
