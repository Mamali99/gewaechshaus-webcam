#  Gewächshaus Webcam Plugin für thin-edge.io mit Tomatenreife-Erkennung

Dieses Plugin für thin-edge.io kombiniert Webcam-Streaming mit KI-gestützter Tomatenreife-Erkennung. Es erfasst Bilder von einer angeschlossenen Webcam, analysiert diese mithilfe eines Machine Learning Modells zur Erkennung des Reifegrads von Tomaten und überträgt die markierten Bilder an Cumulocity IoT.

## Funktionen

- Erfassung von Webcam-Bildern in konfigurierbaren Intervallen
- Automatische Erkennung von Tomaten im Bild mittels Computer Vision
- KI-gestützte Analyse des Reifegrads jeder erkannten Tomate
- Visuelle Markierung der Tomaten (grün für unreif, rot für reif)
- Sichere Übertragung der analysierten Bilder an Cumulocity IoT
- Sichere Handhabung von Zugangsdaten durch Konfigurationsdatei oder Umgebungsvariablen

## Voraussetzungen

- Funktionierendes thin-edge.io System ([Installationsanleitung](https://thin-edge.github.io/thin-edge.io/install/))
- Python 3 und pip3 (Python 2 wird nicht unterstützt)
- Kompatible USB-Webcam (getestet mit Lenovo HD 500)
- Raspberry Pi oder vergleichbarer Linux-Computer

## Installation

1. **System-Updates und grundlegende Bibliotheken**
```bash
sudo apt-get update
sudo apt-get install -y libatlas-base-dev libhdf5-dev python3-pip
```

2. **Python-Abhängigkeiten installieren**
```bash
# Entfernen vorhandener problematischer Pakete
sudo pip3 uninstall numpy opencv-python-headless

# Installation der Pakete von piwheels
sudo pip3 install --only-binary=:all: numpy==1.23.5 --extra-index-url https://www.piwheels.org/simple
sudo pip3 install --only-binary=:all: opencv-python-headless --extra-index-url https://www.piwheels.org/simple
sudo pip3 install --only-binary=:all: tflite-runtime --extra-index-url https://www.piwheels.org/simple
sudo pip3 install --only-binary=:all: imageio imageio-ffmpeg --extra-index-url https://www.piwheels.org/simple
sudo pip3 install requests
```

3. **Projektdateien einrichten**
```bash
# Verzeichnisse erstellen
sudo mkdir -p /etc/tedge/lib/

# Dateien kopieren
sudo cp c8y_Startstream.py /bin/
sudo cp secure_config.py /etc/tedge/lib/
sudo cp tomato_model.tflite /etc/tedge/
sudo cp c8y_Startstream /etc/tedge/operations/c8y/

# Berechtigungen setzen
sudo chmod 555 /bin/c8y_Startstream.py
sudo chmod 555 /etc/tedge/lib/secure_config.py
sudo chmod 644 /etc/tedge/tomato_model.tflite
sudo chmod 644 /etc/tedge/operations/c8y/c8y_Startstream

# Webcam-Bild-Berechtigungen
sudo touch /etc/tedge/webcam_image.jpg
sudo chmod 666 /etc/tedge/webcam_image.jpg
```

4. **Konfiguration einrichten**
```bash
# Credentials-Datei erstellen
sudo touch /etc/tedge/c8y_credentials.json
sudo chmod 600 /etc/tedge/c8y_credentials.json
sudo chown tedge:tedge /etc/tedge/c8y_credentials.json
```

Fügen Sie Ihre Cumulocity IoT Credentials in die Datei ein:
```json
{
    "C8Y_BASEURL": "https://your-tenant.cumulocity.com",
    "TENANT_ID": "your-tenant-id",
    "USERNAME": "your-username",
    "PASSWORD": "your-password"
}
```

Alternativ können Sie die Credentials als Umgebungsvariablen setzen:
```bash
export C8Y_BASEURL="https://your-tenant.cumulocity.com"
export C8Y_TENANT="your-tenant-id"
export C8Y_USERNAME="your-username"
export C8Y_PASSWORD="your-password"
```

5. **Webcam-Zugriff einrichten**
```bash
sudo adduser tedge video
sudo usermod -a -G video tedge
sudo reboot
```

6. **Cumulocity IoT SmartREST Template einrichten**

Erstellen Sie ein SmartREST 2.0 Template in der Cumulocity IoT UI:
- ID: `greenhousewebcam`
- Response ID: `541`
- Name: `c8y_Startstream`
- Base pattern: -
- Condition: `c8y_Startstream`
- Patterns:
    - `deviceId`
    - `c8y_Startstream.parameters.timeout_minutes`

Registrieren Sie das Template auf dem Gerät:
```bash
sudo tedge config set c8y.smartrest.templates greenhousewebcam
```

7. **Thin-edge.io neu verbinden**
```bash
sudo tedge disconnect c8y
sudo tedge connect c8y
sudo systemctl restart tedge_mapper
```

## Verwendung

Nach erfolgreicher Installation können Sie die Aufnahme über die Cumulocity IoT REST API starten:

```bash
curl --location '<url>/devicecontrol/operations/' \
--header 'Authorization: Basic <base64(tenantid/username:password>)' \
--header 'Content-Type: application/json' \
--header 'Accept: application/vnd.com.nsn.cumulocity.operation+json;' \
--data '{
  "deviceId" : "<your-device-id>",
  "c8y_Startstream": {
    "parameters": {
      "timeout_minutes": "5"
    }
  },
  "description": "Start the stream"
}'
```

## Sicherheitsaspekte

Das Projekt implementiert mehrere Sicherheitsmaßnahmen:
- Sichere Speicherung von Credentials durch separate Konfigurationsdatei
- Restriktive Dateiberechtigungen für sensible Daten
- Flexibilität durch Unterstützung von Umgebungsvariablen
- Automatische Fehlerbehandlung bei fehlenden oder ungültigen Credentials

## Entwicklung und Beiträge

1. Repository klonen
2. Abhängigkeiten installieren
3. Eigene Credentials konfigurieren
4. Änderungen testen
5. Pull Request erstellen

## Bekannte Probleme und Einschränkungen

- Die Bilderkennung funktioniert am besten bei guten Lichtverhältnissen
- Das Modell ist auf rote Tomaten trainiert und erkennt möglicherweise andere Tomatensorten nicht optimal
- Die Webcam muss USB Video Class (UVC) kompatibel sein

## Zukünftige Entwicklung

- [ ] Integration weiterer Tomatenarten
- [ ] Verbesserung der Erkennungsgenauigkeit bei schlechten Lichtverhältnissen
- [ ] Erweiterung um zusätzliche Gemüsesorten
- [ ] Integration von Umgebungssensoren (Temperatur, Luftfeuchtigkeit)
- [ ] Konfigurationsmöglichkeiten über Cumulocity IoT UI

## Lizenz

[MIT License](LICENSE)

## Autor

Mohammad Ghalandari (Novatec Consulting GmbH)

## Danksagung

- Novatec Consulting GmbH für die Unterstützung des Projekts
- thin-edge.io Community für die ausgezeichnete IoT-Plattform
- Alle Beitragenden und Tester
