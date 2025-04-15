import RPi.GPIO as GPIO
import time

# Configuration des broches GPIO
RS = 8
ENABLE = 9
D4 = 10
D5 = 11
D6 = 12
D7 = 13

# Configuration des broches en sortie
GPIO.setmode(GPIO.BCM)
GPIO.setup(RS, GPIO.OUT)
GPIO.setup(ENABLE, GPIO.OUT)
GPIO.setup(D4, GPIO.OUT)
GPIO.setup(D5, GPIO.OUT)
GPIO.setup(D6, GPIO.OUT)
GPIO.setup(D7, GPIO.OUT)


# Fonction pour envoyer des données en 4 bits
def lcd_send(data, is_command):
    GPIO.output(RS, GPIO.LOW if is_command else GPIO.HIGH)  # Mode commande ou donnée

    # Envoi des bits hauts
    GPIO.output(D4, (data >> 4) & 0x01)
    GPIO.output(D5, (data >> 5) & 0x01)
    GPIO.output(D6, (data >> 6) & 0x01)
    GPIO.output(D7, (data >> 7) & 0x01)
    lcd_toggle_enable()

    # Envoi des bits bas
    GPIO.output(D4, data & 0x01)
    GPIO.output(D5, (data >> 1) & 0x01)
    GPIO.output(D6, (data >> 2) & 0x01)
    GPIO.output(D7, (data >> 3) & 0x01)
    lcd_toggle_enable()


# Fonction pour activer la broche Enable
def lcd_toggle_enable():
    GPIO.output(ENABLE, GPIO.HIGH)
    time.sleep(0.000001)  # Pause pour signaler la commande (1 microseconde)
    GPIO.output(ENABLE, GPIO.LOW)
    time.sleep(0.00005)  # Délai d'attente (50 microsecondes)


# Initialisation de l'écran LCD
def lcd_init():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(RS, GPIO.OUT)
    GPIO.setup(ENABLE, GPIO.OUT)
    GPIO.setup(D4, GPIO.OUT)
    GPIO.setup(D5, GPIO.OUT)
    GPIO.setup(D6, GPIO.OUT)
    GPIO.setup(D7, GPIO.OUT)

    time.sleep(0.05)  # Pause après l'allumage

    # Initialisation en mode 4 bits
    lcd_send(0x03, True)
    lcd_send(0x03, True)
    lcd_send(0x03, True)
    lcd_send(0x02, True)  # Passer en mode 4 bits

    # Configuration de l'écran
    lcd_send(0x28, True)  # Mode 4 bits, 2 lignes, 5x8 points
    lcd_send(0x0C, True)  # Affichage activé, curseur désactivé
    lcd_send(0x06, True)  # Incrémentation automatique
    lcd_clear()


# Effacer l'écran
def lcd_clear():
    lcd_send(0x01, True)
    time.sleep(0.002)  # Délai d'attente (2 millisecondes)


# Positionner le curseur
def lcd_set_cursor(line, column):
    addr = 0x80 + (0x40 * line) + column
    lcd_send(addr, True)


# Fonction pour afficher un texte
def lcd_write(message):
    if not isinstance(message, str):
        raise ValueError(
            f"lcd_write() attend une chaîne, mais a reçu : {type(message)}"
        )

    max_length = 16
    lines = [message[i : i + max_length] for i in range(0, len(message), max_length)]

    for i, line in enumerate(lines):
        lcd_set_cursor(i, 0)
        for char in line:
            lcd_send(ord(char), False)


# # Programme principal
# try:
#     lcd_init()
#     print("LCD initialisé.")

#     # Exemple d'affichage
#     lcd_set_cursor(0, 0)  # Ligne 1, colonne 0
#     lcd_write("Hello FaceX!")
#     print("Message affiché : Hello FaceX!")

#     lcd_set_cursor(1, 0)  # Ligne 2, colonne 0
#     lcd_write("Bienvenue")
#     print("Message affiché : Bienvenue")

# finally:
#     # Nettoyer les broches GPIO en quittant
#     GPIO.cleanup()
#     print("GPIO nettoyées.")
