import subprocess
import sys
import time
import csv
import threading
from datetime import datetime
from pathlib import Path

# ================================
# PSUTIL – installation automatique
# ================================
def installer_psutil():
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
    except subprocess.CalledProcessError:
        print("Impossible d’installer psutil automatiquement.")
        sys.exit(1)

def charger_psutil():
    try:
        import psutil
        return psutil
    except ImportError:
        installer_psutil()
        import psutil
        return psutil

psutil = charger_psutil()


# ================================
# ANSI couleurs
# ================================
class Couleur:
    RESET = "\033[0m"
    VERT = "\033[32m"
    JAUNE = "\033[33m"
    ROUGE = "\033[31m"
    CYAN = "\033[36m"
    BLEU = "\033[34m"


def couleur_batterie(p):
    if p >= 50:
        return Couleur.VERT
    elif p >= 20:
        return Couleur.JAUNE
    else:
        return Couleur.ROUGE


# ================================
# CSV Journalisation
# ================================
def chemin_csv():
    # Stocke le fichier dans le même dossier que l’exécutable
    base = Path(getattr(sys, '_MEIPASS', Path().absolute()))
    return (base / "batterie_log.csv")


def initialiser_csv(path):
    if not path.exists():
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Heure", "Pourcentage", "Source", "Temps_écoulé"])


def ecrire_csv(path, heure, pourcentage, source, temps):
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([heure, pourcentage, source, temps])


# ================================
# GUI Tkinter
# ================================
def lancer_gui(observer):
    try:
        import tkinter as tk
    except ImportError:
        return   # pas de GUI si Tkinter absent

    fen = tk.Tk()
    fen.title("Surveillance Batterie")

    label = tk.Label(fen, text="", font=("Arial", 16), padx=20, pady=20)
    label.pack()

    def update():
        texte = (
            f"Heure : {observer['heure']}\n"
            f"Batterie : {observer['pourcentage']}% ({observer['source']})\n"
            f"Temps écoulé : {observer['temps']}"
        )
        label.config(text=texte)
        fen.after(1000, update)

    update()
    fen.mainloop()


# ================================
# Affichage principal
# ================================
def afficher_batterie():
    debut = time.time()
    csv_path = chemin_csv()
    initialiser_csv(csv_path)

    observer = {"heure": "", "pourcentage": "", "source": "", "temps": ""}

    threading.Thread(target=lancer_gui, args=(observer,), daemon=True).start()

    print(Couleur.CYAN + "\n--- MONITEUR BATTERIE WINDOWS ---\n" + Couleur.RESET)

    while True:
        batt = psutil.sensors_battery()
        if batt is None:
            print("Aucune batterie détectée.")
            break

        p = batt.percent
        src = "Secteur" if batt.power_plugged else "Batterie"
        col = couleur_batterie(p)

        heure = datetime.now().strftime("%H:%M:%S")

        ec = int(time.time() - debut)
        h, m, s = ec // 3600, (ec % 3600) // 60, ec % 60
        temps = f"{h:02d}h {m:02d}m {s:02d}s"

        observer["heure"] = heure
        observer["pourcentage"] = p
        observer["source"] = src
        observer["temps"] = temps

        ecrire_csv(csv_path, heure, p, src, temps)

        print(
            f"{Couleur.BLEU}Heure{Couleur.RESET}: {heure} | "
            f"{col}Batterie{Couleur.RESET}: {p}% ({src}) | "
            f"{Couleur.CYAN}Temps écoulé{Couleur.RESET}: {temps}"
        )

        time.sleep(1)


# ================================
# Main
# ================================
if __name__ == "__main__":
    afficher_batterie()
