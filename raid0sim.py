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

def controleer_bestanden_en_verplaats(src, disk1, disk2, laatste_schijf):
    # Initialiseer nieuwe_laatste_schijf met de huidige laatste_schijf
    nieuwe_laatste_schijf = laatste_schijf
    
    # Verkrijg de lijst van bestanden in de bronmap
    files = [f for f in os.listdir(src) if os.path.isfile(os.path.join(src, f))]

    tijd_limiet = timedelta(hours=12)
    huidige_tijd = datetime.now()
    bestanden_om_te_verplaatsen = []

    for file in files:
        source_path = os.path.join(src, file)
        wijziging_datum = laatst_gewijzigd(source_path)
        
        if huidige_tijd - wijziging_datum > tijd_limiet:
            bestanden_om_te_verplaatsen.append(file)
        else:
            print(f"{file} is te recent gewijzigd en wordt niet verplaatst.")

    # Verplaats bestanden direct, beginnend met de tegenovergestelde schijf van laatste_schijf
    print("\nStart met verplaatsen van bestanden:")
    for file in bestanden_om_te_verplaatsen:
        source_path = os.path.join(src, file)
        file_size_gb = bestand_grootte(source_path) // (2**30)
        required_space = file_size_gb + 5

        # Kies de andere schijf dan de laatste keer
        if nieuwe_laatste_schijf == 'disk1':
            target_disk = disk2
            target_disk_name = 'disk2'
        else:
            target_disk = disk1
            target_disk_name = 'disk1'
        
        print(f"Bestand: {file}, Grootte: {file_size_gb} GB, Vereiste ruimte: {required_space} GB")
        print(f"Poging tot verplaatsen naar {target_disk_name}")

        if voldoende_vrije_ruimte(target_disk, required_space):
            destination_path = os.path.join(target_disk, file)
            shutil.move(source_path, destination_path)
            print(f"{file} verplaatst naar {target_disk}")
            # Update laatste_schijf voor het volgende bestand
            nieuwe_laatste_schijf = target_disk_name
            # Update config met nieuwe laatste_schijf
            config = lees_config()
            config['laatste_schijf'] = nieuwe_laatste_schijf
            sla_config_op(config)
        else:
            print(f"Niet genoeg ruimte voor {file} op {target_disk_name}, bestand wordt overgeslagen.")

    print("\nVerplaatsing van bestanden is voltooid!")
    return nieuwe_laatste_schijf

# Probeer de configuratie te laden, anders vraag om input
config = lees_config()

if config:
    print("Config geladen uit config.yml:")
    src = config.get('src', '') or input("Geef het pad naar de input map: ")
    disk1 = config.get('disk1', '') or input("Geef het pad naar disk 1: ")
    disk2 = config.get('disk2', '') or input("Geef het pad naar disk 2: ")
    laatste_schijf = config.get('laatste_schijf', 'disk1')  # Standaard disk1
else:
    # Vraag om input als er geen config bestand is
    src = input("Geef het pad naar de input map: ")
    disk1 = input("Geef het pad naar disk 1: ")
    disk2 = input("Geef het pad naar disk 2: ")
    laatste_schijf = 'disk1'  # Begin met disk1

# Sla de instellingen op in config.yml
sla_config_op({
    'src': src,
    'disk1': disk1,
    'disk2': disk2,
    'laatste_schijf': laatste_schijf
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
    laatste_schijf = controleer_bestanden_en_verplaats(src, disk1, disk2, laatste_schijf)
    print("======================================================")
    time.sleep(10)  # Wacht 10 seconden voor de volgende controle
