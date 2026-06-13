"""Curated French noun lexicon — the *real-word* gate for live teaching.

The first live Emma run surfaced a sharp limitation: morphological vetting
(``fr_cp_ce1.vet_word``) checks the *shape* of a proposed word, so it correctly
drops irregular ``-al`` exceptions and mis-categorised words — but it cannot
tell a real noun from a hallucination of the right shape. A model that invents
``« éral »`` (well-formed: ends in ``-al``, not a known exception) would have its
fake plural ``« éraux »`` taught as ground truth.

This whitelist closes that hole: a model-proposed word must *also* be a known
French noun to become a teaching item. Correctness beats coverage — it is far
better to reject a legitimate word the lexicon happens not to list (the adapter
oversamples to compensate) than to teach a confidently-wrong plural for a word
that does not exist.

The list is deliberately small and auditable (CP/CE1 common nouns + the words
the built-in banks use). Ingesting the official programme will grow it from a
real lexical resource (the BO word lists / a CC-licensed lexicon), validated the
same way: a word is gradable only if it is *both* well-formed and attested.
"""
from __future__ import annotations

# Common CP/CE1 nouns. Grouped only for readability; membership is flat.
_SCHOOL = {
    "école", "maître", "maîtresse", "élève", "cahier", "gomme", "règle",
    "trousse", "bureau", "fenêtre", "tableau", "stylo", "crayon", "livre",
    "image", "feuille", "leçon",
}
_HOME = {
    "maison", "table", "chaise", "lampe", "porte", "jardin", "chambre", "lit",
    "cuisine", "fenêtre", "mur", "toit", "clé", "robe", "sac", "ferme",
}
_PEOPLE = {
    "ami", "amie", "fille", "garçon", "enfant", "papa", "maman", "frère",
    "sœur", "voisin", "copain", "bébé",
}
_BODY = {
    "main", "pied", "tête", "bouche", "dent", "cheveu", "doigt", "jambe",
    "cœur", "bras", "nez", "voix", "dos", "corps",
}
_ANIMALS = {
    "chat", "chien", "cheval", "animal", "mouton", "vache", "cochon", "lapin",
    "oiseau", "poisson", "lion", "ours", "renard", "loup", "souris", "tigre",
    "poule", "canard", "âne", "chèvre",
}
_FOOD = {
    "pomme", "poire", "fraise", "cerise", "banane", "carotte", "tomate",
    "pain", "gâteau", "bonbon", "eau", "lait", "riz", "repas", "noix",
}
_NATURE = {
    "soleil", "lune", "étoile", "ciel", "mer", "plage", "forêt", "rivière",
    "montagne", "nuage", "arbre", "fleur", "bois", "pré", "champ", "île",
}
_PLACES = {
    "ville", "village", "rue", "route", "magasin", "boulangerie", "gare",
    "pont", "hôpital", "hôtel", "château", "tribunal", "terminal", "canal",
}
_OBJECTS = {
    "voiture", "vélo", "camion", "avion", "bateau", "fusée", "train",
    "ballon", "guitare", "journal", "bocal", "métal", "signal", "prix",
    "croix", "tas", "pays", "choix", "gaz", "végétal", "cardinal", "total",
    "rival", "général", "local",
}
# Words used by the transfer banks — must be attested so the held-out / transfer
# ground truth is itself a real plural.
_TRANSFER = {
    "minéral", "littoral", "amiral", "arsenal", "maréchal", "caporal",
}

NOUNS: frozenset[str] = frozenset(
    _SCHOOL | _HOME | _PEOPLE | _BODY | _ANIMALS | _FOOD | _NATURE
    | _PLACES | _OBJECTS | _TRANSFER
)


def in_lexicon(word: str) -> bool:
    """Is ``word`` an attested French noun this curriculum can grade?"""
    return word.strip().lower() in NOUNS
