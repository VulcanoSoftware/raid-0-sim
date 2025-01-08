import os
from datetime import datetime, timedelta
import shutil
import yaml
import time

# Bepaal het pad voor de config.yml
huidig_pad = os.getcwd()
conf_pad = os.path.join(huidig_pad, "config.yml")

def laatst_gewijzigd(path):
    # Verkrijg de laatste wijzigingsdatum van een bestand
    laatst_wijziging_timestamp = os.path.getmtime(path)
    laatst_wijziging_datum = datetime.fromtimestamp(laatst_wijziging_timestamp)
    return laatst_wijziging_datum

def bestand_grootte(path):
    # Verkrijg de grootte van het bestand in bytes
    return os.path.getsize(path)

def voldoende_vrije_ruimte(disk, vereiste_gb):
    # Verkrijg de beschikbare ruimte op de schijf
    totaal, gebruikt, vrij = shutil.disk_usage(disk)
    
    # Zet de vrije ruimte om naar GB
    vrij_gb = vrij // (2**30)  # Omrekenen van bytes naar GB
    
    # Controleer of er voldoende vrije ruimte is
    if vrij_gb >= vereiste_gb:
        return True
    else:
        return False

def sla_config_op(config_data, config_path=conf_pad):
    # Sla de configuratie op in het config.yml bestand
    with open(config_path, 'w') as yaml_file:
        yaml.dump(config_data, yaml_file, default_flow_style=False)

def lees_config(config_path=conf_pad):
    # Lees de configuratie uit config.yml
    if os.path.exists(config_path):
        with open(config_path, 'r') as yaml_file:
            config_data = yaml.safe_load(yaml_file)
            print(f"Config data geladen: {config_data}")  # Debugging line to check what's being loaded
            return config_data
    else:
        return None

def controleer_bestanden_en_verplaats(src, disk1, disk2):
    # Verkrijg de lijst van bestanden in de bronmap
    files = [f for f in os.listdir(src) if os.path.isfile(os.path.join(src, f))]

    # De tijdsduur waarvoor een bestand niet gewijzigd mag zijn
    tijd_limiet = timedelta(hours=12)
    huidige_tijd = datetime.now()

    # Lijst van bestanden die langer dan 12 uur niet gewijzigd zijn
    bestanden_om_te_verplaatsen = []

    # Verzamelen van bestanden die voldoen aan de tijdscontrole
    for file in files:
        source_path = os.path.join(src, file)
        wijziging_datum = laatst_gewijzigd(source_path)
        
        if huidige_tijd - wijziging_datum > tijd_limiet:
            bestanden_om_te_verplaatsen.append(file)
        else:
            print(f"{file} is te recent gewijzigd en wordt niet verplaatst.")

    # Verdeel de bestanden in twee groepen
    disk1_files = []
    disk2_files = []

    # Bereken de benodigde ruimte voor elk bestand
    for file in bestanden_om_te_verplaatsen:
        source_path = os.path.join(src, file)
        file_size_gb = bestand_grootte(source_path) // (2**30)  # Bestandsgrootte in GB
        required_space = file_size_gb + 5  # Voeg 5 GB toe aan de bestandsgrootte
        
        # Print de bestandsgrootte en de vereiste ruimte
        print(f"Bestand: {file}, Grootte: {file_size_gb} GB, Vereiste ruimte: {required_space} GB")
        
        # Controleer of er voldoende ruimte is op de schijven en verdeel de bestanden
        if voldoende_vrije_ruimte(disk1, required_space):
            disk1_files.append(file)
        elif voldoende_vrije_ruimte(disk2, required_space):
            disk2_files.append(file)
        else:
            print(f"Niet genoeg ruimte voor {file} op beide schijven.")
    
    # Verplaats de bestanden naar de respectieve schijven
    print("\nStart met verplaatsen van bestanden:")
    for file in disk1_files:
        source_path = os.path.join(src, file)
        destination_path = os.path.join(disk1, file)
        required_space = bestand_grootte(source_path) // (2**30) + 5
        print(f"Verplaatsing van {file} naar {disk1}, Vereiste ruimte: {required_space} GB")
        shutil.move(source_path, destination_path)
        print(f"{file} verplaatst naar {disk1}")

    for file in disk2_files:
        source_path = os.path.join(src, file)
        destination_path = os.path.join(disk2, file)
        required_space = bestand_grootte(source_path) // (2**30) + 5
        print(f"Verplaatsing van {file} naar {disk2}, Vereiste ruimte: {required_space} GB")
        shutil.move(source_path, destination_path)
        print(f"{file} verplaatst naar {disk2}")

    print("\nVerplaatsing van bestanden is voltooid!")

# Probeer de configuratie te laden, anders vraag om input
config = lees_config()

if config:
    print("Config geladen uit config.yml:")
    src = config.get('src', '') or input("Geef het pad naar de input map: ")
    disk1 = config.get('disk1', '') or input("Geef het pad naar disk 1: ")
    disk2 = config.get('disk2', '') or input("Geef het pad naar disk 2: ")
else:
    # Vraag om input als er geen config bestand is
    src = input("Geef het pad naar de input map: ")
    disk1 = input("Geef het pad naar disk 1: ")
    disk2 = input("Geef het pad naar disk 2: ")

# Sla de instellingen op in config.yml
sla_config_op({
    'src': src,
    'disk1': disk1,
    'disk2': disk2
})

# Controleer of de opgegeven mappen bestaan
if not os.path.exists(src):
    print(f"De bronmap {src} bestaat niet.")
    exit()
for disk in [disk1, disk2]:
    if not os.path.exists(disk):
        print(f"De map {disk} bestaat niet. Ik maak de map aan.")
        os.makedirs(disk)

# Zorg ervoor dat het programma altijd blijft draaien en elke 10 seconden de inhoud controleert
while True:
    print("======================================================")
    controleer_bestanden_en_verplaats(src, disk1, disk2)
    print("======================================================")
    time.sleep(10)  # Wacht 10 seconden voor de volgende controle
