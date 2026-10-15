"""Moteur temporel : fait évoluer les cours toutes les 30 secondes."""
import random
import time

import gestionnaire_json as gj

INTERVALLE = 30          # secondes entre deux cycles (ticks)
PROBA_CHOC = 0.25        # 1 chance sur 4 d'avoir une actualité choc
PRIX_MINIMUM = 0.50      # un cours ne tombe jamais à zéro

ACTUS_POSITIVES = [
    "Nouvelle puce révolutionnaire",
    "Succès commercial inattendu",
    "Contrat géant signé avec l'État",
    "Résultats trimestriels record",
]
ACTUS_NEGATIVES = [
    "Rappel de produits défectueux",
    "Enquête des autorités",
    "Cyberattaque sur les serveurs",
    "Grève générale des employés",
]


def appliquer_variation(entreprise, pourcentage):
    """Modifie le prix d'une entreprise et mémorise la variation."""
    nouveau = entreprise["prix"] * (1 + pourcentage / 100)
    entreprise["prix"] = round(max(nouveau, PRIX_MINIMUM), 2)
    entreprise["variation"] = round(pourcentage, 2)


def faire_un_cycle():
    """Un tick : variations aléatoires -3 % à +3 %, puis éventuelle actualité choc."""
    with gj.verrou:
        marche = gj.charger_fichier("marche.json")
        entreprises = marche["entreprises"]

        # 1) fluctuation standard pour chaque entreprise
        for entreprise in entreprises.values():
            appliquer_variation(entreprise, random.uniform(-3, 3))

        # 2) tirage d'une actualité choc (25 %)
        if random.random() < PROBA_CHOC:
            symbole = random.choice(list(entreprises))
            if random.random() < 0.5:
                choc = round(random.uniform(5, 15), 1)
                texte = random.choice(ACTUS_POSITIVES)
            else:
                choc = round(random.uniform(-20, -5), 1)
                texte = random.choice(ACTUS_NEGATIVES)
            appliquer_variation(entreprises[symbole], choc)
            marche["derniere_actu"] = f"[{symbole}] {texte} ({choc:+.0f}%)"
            gj.ajouter_evenement(marche["derniere_actu"], symbole, choc)

        gj.sauvegarder_fichier("marche.json", marche)
        gj.enregistrer_cours(marche)
        return marche


# Instant (time.time) du prochain cycle : affiché par le tableau de bord
prochain_cycle = time.time() + INTERVALLE


def boucle_simulation():
    """Boucle infinie, destinée à tourner dans un thread."""
    global prochain_cycle
    while True:
        prochain_cycle = time.time() + INTERVALLE
        time.sleep(INTERVALLE)
        faire_un_cycle()
