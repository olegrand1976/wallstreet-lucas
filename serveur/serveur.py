"""Serveur central du Marché Virtuel : API HTTP/JSON (Flask)."""
import random
import threading
import time

from flask import Flask, jsonify, request, send_from_directory

import gestionnaire_json as gj
import simulation

app = Flask(__name__)


def erreur(message, code=400):
    return jsonify({"succes": False, "erreur": message}), code


def valeur_portefeuille(joueur, entreprises):
    """Solde + valeur estimée des actions (arrondi à 2 décimales)."""
    total = joueur["solde"]
    for symbole, quantite in joueur["actions"].items():
        if symbole in entreprises:
            total += quantite * entreprises[symbole]["prix"]
    return round(total, 2)


def description_compte(joueur, marche):
    return {
        "pseudo": joueur["pseudo"],
        "solde": round(joueur["solde"], 2),
        "actions": joueur["actions"],
        "valeur_totale": valeur_portefeuille(joueur, marche["entreprises"]),
    }


@app.route("/")
def accueil():
    """Tableau de bord de visualisation du marché."""
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/historique", methods=["GET"])
def historique():
    """Courbes, évènements, transactions et état du marché (pour le tableau de bord)."""
    with gj.verrou:
        histo = gj.charger_fichier("historique.json")
        marche = gj.charger_fichier("marche.json")
    return jsonify({
        **histo,
        "marche": marche,
        "intervalle": simulation.INTERVALLE,
        "secondes_restantes": max(0, round(simulation.prochain_cycle - time.time())),
    })


@app.route("/api/connexion", methods=["POST"])
def connexion():
    """Inscription ou reconnexion d'un joueur."""
    donnees = request.get_json(silent=True) or {}
    pseudo = str(donnees.get("pseudo", "")).strip()
    if not pseudo:
        return erreur("Pseudo manquant.")
    cle = pseudo.lower()

    with gj.verrou:
        joueurs = gj.charger_fichier("joueurs.json")
        nouveau = cle not in joueurs
        if nouveau:
            marche = gj.charger_fichier("marche.json")
            joueurs[cle] = {
                "pseudo": pseudo,
                "solde": round(random.uniform(100, 1000), 2),
                "actions": {symbole: 0 for symbole in marche["entreprises"]},
            }
            gj.sauvegarder_fichier("joueurs.json", joueurs)
        marche = gj.charger_fichier("marche.json")
        compte = description_compte(joueurs[cle], marche)

    return jsonify({"succes": True, "nouveau": nouveau, **compte})


@app.route("/api/cours", methods=["GET"])
def cours():
    """Prix, variations et dernière actualité."""
    return jsonify(gj.charger_fichier("marche.json"))


@app.route("/api/compte/<pseudo>", methods=["GET"])
def compte(pseudo):
    """Solde et portefeuille d'un joueur."""
    with gj.verrou:
        joueurs = gj.charger_fichier("joueurs.json")
        marche = gj.charger_fichier("marche.json")
    joueur = joueurs.get(pseudo.strip().lower())
    if joueur is None:
        return erreur("Joueur inconnu.", 404)
    return jsonify({"succes": True, **description_compte(joueur, marche)})


@app.route("/api/ordre", methods=["POST"])
def ordre():
    """Achat ou vente d'actions."""
    donnees = request.get_json(silent=True) or {}
    cle = str(donnees.get("pseudo", "")).strip().lower()
    symbole = str(donnees.get("symbole", "")).strip().upper()
    type_ordre = str(donnees.get("type_ordre", "")).strip().upper()

    try:
        quantite = int(donnees.get("quantite"))
    except (TypeError, ValueError):
        return erreur("La quantité doit être un nombre entier.")
    if quantite <= 0:
        return erreur("La quantité doit être strictement positive.")
    if type_ordre not in ("ACHAT", "VENTE"):
        return erreur("Type d'ordre invalide (ACHAT ou VENTE).")

    # Tout le traitement est sous verrou : lecture, vérification, écriture.
    with gj.verrou:
        joueurs = gj.charger_fichier("joueurs.json")
        marche = gj.charger_fichier("marche.json")

        joueur = joueurs.get(cle)
        if joueur is None:
            return erreur("Joueur inconnu.", 404)
        if symbole not in marche["entreprises"]:
            return erreur(f"Symbole inconnu : {symbole}.")

        prix = marche["entreprises"][symbole]["prix"]
        montant = round(quantite * prix, 2)
        detenues = joueur["actions"].get(symbole, 0)

        if type_ordre == "ACHAT":
            if joueur["solde"] < montant:
                return erreur(
                    f"Solde insuffisant : il faut {montant:.2f} € "
                    f"mais tu as {joueur['solde']:.2f} €."
                )
            joueur["solde"] = round(joueur["solde"] - montant, 2)
            joueur["actions"][symbole] = detenues + quantite
            message = f"Achat de {quantite} {symbole} à {prix:.2f} € = {montant:.2f} €."
        else:
            if detenues < quantite:
                return erreur(
                    f"Actions insuffisantes : tu possèdes {detenues} {symbole}, "
                    f"tu veux en vendre {quantite}."
                )
            joueur["solde"] = round(joueur["solde"] + montant, 2)
            joueur["actions"][symbole] = detenues - quantite
            message = f"Vente de {quantite} {symbole} à {prix:.2f} € = {montant:.2f} €."

        gj.sauvegarder_fichier("joueurs.json", joueurs)
        gj.ajouter_transaction(joueur["pseudo"], type_ordre, symbole, quantite, prix, montant)
        resume = description_compte(joueur, marche)

    return jsonify({"succes": True, "message": message, **resume})


if __name__ == "__main__":
    gj.initialiser_donnees()
    threading.Thread(target=simulation.boucle_simulation, daemon=True).start()
    print("Serveur du Marché Virtuel actif sur http://0.0.0.0:5000")
    print(f"Cycle de simulation : {simulation.INTERVALLE} s - Ctrl+C pour arrêter")
    # host 0.0.0.0 : accessible depuis les PC élèves du réseau local
    app.run(host="0.0.0.0", port=5000, threaded=True, use_reloader=False)
