"""Charge le jeu de test de 50 actions dans le marché.

À lancer avec le serveur ARRÊTÉ :
    python charger_jeu_test.py                  -> remet aussi à zéro l'historique et les joueurs
    python charger_jeu_test.py --garder-joueurs -> conserve joueurs.json

Pour revenir au marché de départ (5 entreprises) : supprimer data/marche.json
et data/historique.json, le serveur les recrée au prochain démarrage.
"""
import os
import shutil
import sys

DOSSIER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
SOURCE = os.path.join(DOSSIER, "jeu_test_50.json")


def supprimer(nom):
    chemin = os.path.join(DOSSIER, nom)
    if os.path.exists(chemin):
        os.remove(chemin)
        print(f"  supprimé : {nom}")


if not os.path.exists(SOURCE):
    sys.exit("Fichier data/jeu_test_50.json introuvable.")

shutil.copyfile(SOURCE, os.path.join(DOSSIER, "marche.json"))
print("marche.json remplacé par le jeu de test (50 actions).")

supprimer("historique.json")          # les anciennes courbes n'ont plus de sens
if "--garder-joueurs" not in sys.argv:
    supprimer("joueurs.json")         # recréé vide au démarrage du serveur

print("Terminé. Tu peux relancer serveur.py.")
