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
    return vrij_gb >= vereiste_gb

def sla_config_op(config_data, config_path=conf_pad):
    with open(config_path, 'w') as yaml_file:
        yaml.dump(config_data, yaml_file, default_flow_style=False)

def lees_config(config_path=conf_pad):
    if os.path.exists(config_path):
        with open(config_path, 'r') as yaml_file:
            config_data = yaml.safe_load(yaml_file)
            print(f"Config data geladen: {config_data}")
            return config_data
    return None

def stuur_discord_bericht(bericht, webhook_url):
    if not webhook_url:  # Als er geen webhook URL is ingevuld, stuur dan geen bericht
        return
    try:
        data = {
            "content": bericht,
            "avatar_url": "https://www.dropbox.com/scl/fi/o4kv0p6mw1bmr2wfpbxmw/raid0sim.png?rlkey=6644crh1cu5usbd4luormduh0&st=2e19ktx7&dl=1"
        }
        requests.post(webhook_url, json=data)
    except Exception as e:
        print(f"Fout bij versturen Discord bericht: {e}")

def print_en_discord(bericht, webhook_url):
    print(bericht)  # Altijd naar console printen
    stuur_discord_bericht(bericht, webhook_url)  # Alleen naar Discord als webhook_url is ingevuld

def krijg_volgende_schijf(huidige_schijf, schijven):
    """Bepaalt welke schijf de volgende is in de rotatie."""
    huidige_index = schijven.index(huidige_schijf)
    volgende_index = (huidige_index + 1) % len(schijven)
    return schijven[volgende_index]

def vraag_schijf_info(schijf_nummer):
    """Vraagt informatie over een specifieke schijf."""
    pad = input(f"Geef het pad naar schijf {schijf_nummer}: ")
    naam = f"disk{schijf_nummer}"
    return {
        'pad': pad,
        'naam': naam
    }

def controleer_bestanden_en_verplaats(src, schijven, laatste_schijf, webhook_url):
    nieuwe_laatste_schijf = laatste_schijf
    files = [f for f in os.listdir(src) if os.path.isfile(os.path.join(src, f))]

    tijd_limiet = timedelta(hours=4)
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

        # Probeer elke schijf totdat we er een vinden met genoeg ruimte
        bestand_verplaatst = False
        originele_schijf = nieuwe_laatste_schijf
        target_schijf = krijg_volgende_schijf(nieuwe_laatste_schijf, [schijf['naam'] for schijf in schijven])

        for _ in range(len(schijven)):
            target_info = next(schijf for schijf in schijven if schijf['naam'] == target_schijf)
            target_pad = target_info['pad']

            print_en_discord(f"Bestand: {file}, Grootte: {file_size_gb} GB, Vereiste ruimte: {required_space} GB", webhook_url)
            print_en_discord(f"Poging tot verplaatsen naar {target_schijf}", webhook_url)

            if voldoende_vrije_ruimte(target_pad, required_space):
                destination_path = os.path.join(target_pad, file)
                shutil.move(source_path, destination_path)
                print_en_discord(f"{file} verplaatst naar {target_schijf}", webhook_url)
                nieuwe_laatste_schijf = target_schijf
                bestand_verplaatst = True
                break
            else:
                print_en_discord(f"Niet genoeg ruimte voor {file} op {target_schijf}", webhook_url)
                target_schijf = krijg_volgende_schijf(target_schijf, [schijf['naam'] for schijf in schijven])

        if not bestand_verplaatst:
            print_en_discord(f"Geen schijf heeft genoeg ruimte voor {file}, bestand wordt overgeslagen.", webhook_url)

    print_en_discord("\nVerplaatsing van bestanden is voltooid!", webhook_url)
    return nieuwe_laatste_schijf

def main():
    config = lees_config()
    
    if config:
        print("Config geladen uit config.yml:")
        src = config.get('src', '') or input("Geef het pad naar de input map: ")
        webhook_url = config.get('webhook_url', '')
        if webhook_url is None:  # Als webhook_url niet in config staat
            webhook_input = input("Geef de Discord webhook URL (laat leeg om Discord meldingen uit te schakelen): ")
            webhook_url = webhook_input if webhook_input.strip() else ""
        schijven = config.get('schijven', [])
        laatste_schijf = config.get('laatste_schijf', '')
        
        if not schijven:
            aantal_schijven = int(input("Hoeveel schijven wil je toevoegen? "))
            schijven = [vraag_schijf_info(i + 1) for i in range(aantal_schijven)]
            laatste_schijf = schijven[0]['naam']
    else:
        src = input("Geef het pad naar de input map: ")
        webhook_input = input("Geef de Discord webhook URL (laat leeg om Discord meldingen uit te schakelen): ")
        webhook_url = webhook_input if webhook_input.strip() else ""
        aantal_schijven = int(input("Hoeveel schijven wil je toevoegen? "))
        schijven = [vraag_schijf_info(i + 1) for i in range(aantal_schijven)]
        laatste_schijf = schijven[0]['naam']

    # Config opslaan
    config_data = {
        'src': src,
        'webhook_url': webhook_url,
        'schijven': schijven,
        'laatste_schijf': laatste_schijf
    }
    sla_config_op(config_data)

    while True:
        try:
            if not os.path.exists(src):
                print_en_discord(f"De bronmap {src} bestaat niet.", webhook_url)
                input("Druk op Enter om opnieuw te proberen...")
                continue

            # Controleer en maak ontbrekende schijfmappen aan
            for schijf in schijven:
                if not os.path.exists(schijf['pad']):
                    print_en_discord(f"De map {schijf['pad']} bestaat niet. Ik maak de map aan.", webhook_url)
                    os.makedirs(schijf['pad'])

            print_en_discord(f"\nScript gestart met de volgende configuratie:", webhook_url)
            print_en_discord(f"Bronmap: {src}", webhook_url)
            for schijf in schijven:
                print_en_discord(f"Schijf {schijf['naam']}: {schijf['pad']}", webhook_url)
            print_en_discord(f"Laatste gebruikte schijf: {laatste_schijf}", webhook_url)

            laatste_clear = datetime.now()
            while True:
                print_en_discord("======================================================", webhook_url)
                laatste_schijf = controleer_bestanden_en_verplaats(src, schijven, laatste_schijf, webhook_url)
                
                # Update config met nieuwe laatste schijf
                config = lees_config()
                config['laatste_schijf'] = laatste_schijf
                sla_config_op(config)
                
                print_en_discord("======================================================", webhook_url)

                if datetime.now() - laatste_clear > timedelta(hours=6):
                    os.system('cls' if os.name == 'nt' else 'clear')
                    laatste_clear = datetime.now()
                    print_en_discord("Console is gewist", webhook_url)

                time.sleep(120)

        except Exception as e:
            print_en_discord(f"Er is een fout opgetreden: {str(e)}", webhook_url)
            input("Druk op Enter om het programma opnieuw te starten...")

if __name__ == "__main__":
    main()

