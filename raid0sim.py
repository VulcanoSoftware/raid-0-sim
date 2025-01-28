import os
from datetime import datetime, timedelta
import shutil
import yaml
import time
import requests 

huidig_pad = os.getcwd()
conf_pad = os.path.join(huidig_pad, "config.yml")

def laatst_gewijzigd(path):
    laatst_wijziging_timestamp = os.path.getmtime(path)
    laatst_wijziging_datum = datetime.fromtimestamp(laatst_wijziging_timestamp)
    return laatst_wijziging_datum

def bestand_grootte(path):
    return os.path.getsize(path)

def voldoende_vrije_ruimte(disk, vereiste_gb):
    totaal, gebruikt, vrij = shutil.disk_usage(disk)
    
    vrij_gb = vrij // (2**30)  
    
    if vrij_gb >= vereiste_gb:
        return True
    else:
        return False

def sla_config_op(config_data, config_path=conf_pad):
    with open(config_path, 'w') as yaml_file:
        yaml.dump(config_data, yaml_file, default_flow_style=False)

def lees_config(config_path=conf_pad):
    if os.path.exists(config_path):
        with open(config_path, 'r') as yaml_file:
            config_data = yaml.safe_load(yaml_file)
            print(f"Config data geladen: {config_data}") 
            return config_data
    else:
        return None

def stuur_discord_bericht(bericht, webhook_url):
    try:
        data = {
            "content": bericht,
            "avatar_url": "https://www.dropbox.com/scl/fi/o4kv0p6mw1bmr2wfpbxmw/raid0sim.png?rlkey=6644crh1cu5usbd4luormduh0&st=2e19ktx7&dl=1"
        }
        requests.post(webhook_url, json=data)
    except Exception as e:
        print(f"Fout bij versturen Discord bericht: {e}")

def print_en_discord(bericht, webhook_url):
    stuur_discord_bericht(bericht, webhook_url)

def controleer_bestanden_en_verplaats(src, disk1, disk2, laatste_schijf):
    nieuwe_laatste_schijf = laatste_schijf
    
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
            print_en_discord(f"{file} is te recent gewijzigd en wordt niet verplaatst.", webhook_url)

    print_en_discord("\nStart met verplaatsen van bestanden:", webhook_url)
    for file in bestanden_om_te_verplaatsen:
        source_path = os.path.join(src, file)
        file_size_gb = bestand_grootte(source_path) // (2**30)
        required_space = file_size_gb + 5

        if nieuwe_laatste_schijf == 'disk1':
            target_disk = disk2
            target_disk_name = 'disk2'
        else:
            target_disk = disk1
            target_disk_name = 'disk1'
        
        print_en_discord(f"Bestand: {file}, Grootte: {file_size_gb} GB, Vereiste ruimte: {required_space} GB", webhook_url)
        print_en_discord(f"Poging tot verplaatsen naar {target_disk_name}", webhook_url)

        if voldoende_vrije_ruimte(target_disk, required_space):
            destination_path = os.path.join(target_disk, file)
            shutil.move(source_path, destination_path)
            print_en_discord(f"{file} verplaatst naar {target_disk}", webhook_url)
            nieuwe_laatste_schijf = target_disk_name
            config = lees_config()
            config['laatste_schijf'] = nieuwe_laatste_schijf
            sla_config_op(config)
        else:
            print_en_discord(f"Niet genoeg ruimte voor {file} op {target_disk_name}, bestand wordt overgeslagen.", webhook_url)

    print_en_discord("\nVerplaatsing van bestanden is voltooid!", webhook_url)
    return nieuwe_laatste_schijf

config = lees_config()

if config:
    print("Config geladen uit config.yml:")
    src = config.get('src', '') or input("Geef het pad naar de input map: ")
    disk1 = config.get('disk1', '') or input("Geef het pad naar disk 1: ")
    disk2 = config.get('disk2', '') or input("Geef het pad naar disk 2: ")
    laatste_schijf = config.get('laatste_schijf', 'disk1')  
    webhook_url = config.get('webhook_url', '') or input("Geef de Discord webhook URL: ")
else:
    src = input("Geef het pad naar de input map: ")
    disk1 = input("Geef het pad naar disk 1: ")
    disk2 = input("Geef het pad naar disk 2: ")
    laatste_schijf = 'disk1' 
    webhook_url = input("Geef de Discord webhook URL: ")

sla_config_op({
    'src': src,
    'disk1': disk1,
    'disk2': disk2,
    'laatste_schijf': laatste_schijf,
    'webhook_url': webhook_url
})

if not os.path.exists(src):
    print_en_discord(f"De bronmap {src} bestaat niet.", webhook_url)
    exit()
for disk in [disk1, disk2]:
    if not os.path.exists(disk):
        print_en_discord(f"De map {disk} bestaat niet. Ik maak de map aan.", webhook_url)
        os.makedirs(disk)

print_en_discord(f"\nScript gestart met de volgende configuratie:", webhook_url)
print_en_discord(f"Bronmap: {src}", webhook_url)
print_en_discord(f"Schijf 1: {disk1}", webhook_url)
print_en_discord(f"Schijf 2: {disk2}", webhook_url)
print_en_discord(f"Laatste gebruikte schijf: {laatste_schijf}", webhook_url)

laatste_clear = datetime.now()
while True:
    huidige_tijd = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print_en_discord(f"\nNieuwe controle gestart op: {huidige_tijd}", webhook_url)
    print_en_discord("======================================================", webhook_url)
    laatste_schijf = controleer_bestanden_en_verplaats(src, disk1, disk2, laatste_schijf)
    print_en_discord("======================================================", webhook_url)
    
    if datetime.now() - laatste_clear > timedelta(hours=6):
        os.system('cls' if os.name == 'nt' else 'clear')
        laatste_clear = datetime.now()
        print_en_discord("Console is gewist", webhook_url)
    
    time.sleep(120) 
