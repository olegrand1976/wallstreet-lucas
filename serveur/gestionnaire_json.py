"""Accès sécurisé aux fichiers JSON (marche.json et joueurs.json)."""
import json
import os
import threading
import time

DOSSIER_DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# Verrou de sécurité : un seul thread à la fois lit/écrit les fichiers.
# RLock = le même thread peut le reprendre (utile pour lecture + écriture imbriquées).
verrou = threading.RLock()

MARCHE_PAR_DEFAUT = {
    "derniere_actu": "Ouverture du marché : bonne séance à tous !",
    "entreprises": {
        "TECH": {"nom": "Nova Technologies", "secteur": "Informatique", "prix": 42.50, "variation": 0.0},
        "BIO":  {"nom": "BioSanté Labs",     "secteur": "Santé",        "prix": 18.20, "variation": 0.0},
        "NRG":  {"nom": "Eco Energie",       "secteur": "Énergie",      "prix": 75.10, "variation": 0.0},
        "AGRI": {"nom": "AgriPlus",          "secteur": "Agriculture",  "prix": 31.00, "variation": 0.0},
        "AUTO": {"nom": "ElectroMotors",     "secteur": "Transport",    "prix": 55.80, "variation": 0.0},
    },
}


def _chemin(nom):
    return os.path.join(DOSSIER_DATA, nom)


def charger_fichier(nom):
    """Lit un fichier JSON du dossier data/ et renvoie un dictionnaire."""
    with verrou:
        with open(_chemin(nom), "r", encoding="utf-8") as fichier:
            return json.load(fichier)


def sauvegarder_fichier(nom, donnees):
    """Écrit un dictionnaire dans un fichier JSON lisible (indent=4)."""
    with verrou:
        with open(_chemin(nom), "w", encoding="utf-8") as fichier:
            json.dump(donnees, fichier, indent=4, ensure_ascii=False)


# --- Historique (pour les courbes et le tableau de bord) -------------------
MAX_POINTS = 120          # points de courbe conservés par entreprise
MAX_EVENEMENTS = 50
MAX_TRANSACTIONS = 100


def enregistrer_cours(marche):
    """Ajoute un point de courbe par entreprise dans historique.json."""
    with verrou:
        histo = charger_fichier("historique.json")
        maintenant = int(time.time())
        for symbole, entreprise in marche["entreprises"].items():
            serie = histo["cours"].setdefault(symbole, [])
            serie.append({"t": maintenant, "prix": entreprise["prix"]})
            del serie[:-MAX_POINTS]
        sauvegarder_fichier("historique.json", histo)


def ajouter_evenement(texte, symbole=None, variation=None):
    """Mémorise une actualité choc."""
    with verrou:
        histo = charger_fichier("historique.json")
        histo["evenements"].append({
            "t": int(time.time()), "texte": texte,
            "symbole": symbole, "variation": variation,
        })
        del histo["evenements"][:-MAX_EVENEMENTS]
        sauvegarder_fichier("historique.json", histo)


def ajouter_transaction(pseudo, type_ordre, symbole, quantite, prix, montant):
    """Mémorise un achat ou une vente réussi."""
    with verrou:
        histo = charger_fichier("historique.json")
        histo["transactions"].append({
            "t": int(time.time()), "pseudo": pseudo, "type_ordre": type_ordre,
            "symbole": symbole, "quantite": quantite,
            "prix": prix, "montant": montant,
        })
        del histo["transactions"][:-MAX_TRANSACTIONS]
        sauvegarder_fichier("historique.json", histo)


def initialiser_donnees():
    """Crée les fichiers manquants au démarrage du serveur."""
    os.makedirs(DOSSIER_DATA, exist_ok=True)
    with verrou:
        if not os.path.exists(_chemin("marche.json")):
            sauvegarder_fichier("marche.json", MARCHE_PAR_DEFAUT)
        if not os.path.exists(_chemin("joueurs.json")):
            sauvegarder_fichier("joueurs.json", {})
        if not os.path.exists(_chemin("historique.json")):
            sauvegarder_fichier("historique.json",
                                {"cours": {}, "evenements": [], "transactions": []})
            # premier point de courbe = cours d'ouverture
            enregistrer_cours(charger_fichier("marche.json"))
