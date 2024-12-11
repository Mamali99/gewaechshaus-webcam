#!/usr/bin/python3
# coding=utf-8
import sys
import requests
import time
import datetime
import imageio as iio
import cv2
import numpy as np
from requests.auth import HTTPBasicAuth
import traceback
import tflite_runtime.interpreter as tflite


# Add the lib directory to Python path
sys.path.append('/etc/tedge/lib')
from secure_config import ConfigHandler

# Load configuration securely
config_handler = ConfigHandler()
config = config_handler.load_config()

# Use configuration values
C8Y_BASEURL = config['C8Y_BASEURL']
TENANT_ID = config['TENANT_ID']
USERNAME = config['USERNAME']
PASSWORD = config['PASSWORD']

USER = f"{TENANT_ID}/{USERNAME}"

auth = HTTPBasicAuth(USERNAME, PASSWORD)

WORKDIR = "/etc/tedge"
IMAGE_NAME = "webcam_image.jpg"
IMAGE_PATH = f"{WORKDIR}/{IMAGE_NAME}"

TYPE = "image/jpeg"

# Frames per Second
FPS = 1 / 30

MODEL_PATH = "/etc/tedge/tomato_model.tflite"

def get_image_id() -> str:
    url = f"{C8Y_BASEURL}/inventory/binaries"
    params = {"pageSize": 2000, "type": TYPE}
    response = requests.get(url, params=params, auth=auth)
    # print (response.json())
    for item in response.json()["managedObjects"]:
        if item["name"] == IMAGE_NAME:
            return item["id"]
            
def adjust_image(image):
    """Adjust image color and brightness"""
    # Weißabgleich und Kontrastverbesserung
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    
    # CLAHE auf L-Kanal anwenden
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    cl = clahe.apply(l)
    
    # Kontrast erhöhen
    cl = cv2.multiply(cl, 1.2)
    
    # Kanäle wieder zusammenfügen
    adjusted = cv2.merge((cl,a,b))
    adjusted = cv2.cvtColor(adjusted, cv2.COLOR_LAB2BGR)
    
    # Gammakorrektur für bessere Sichtbarkeit in dunklen Bereichen
    gamma = 1.5
    lookUpTable = np.empty((1,256), np.uint8)
    for i in range(256):
        lookUpTable[0,i] = np.clip(pow(i / 255.0, 1.0 / gamma) * 255.0, 0, 255)
    adjusted = cv2.LUT(adjusted, lookUpTable)
    
    return adjusted

def detect_tomatoes(image):
    """Detect tomatoes in image using color detection with adjusted parameters"""
    # Bild vorverarbeiten
    image = adjust_image(image)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    # Erweiterte Farbbereiche für verschiedene Lichtverhältnisse
    lower_red1 = np.array([0, 50, 50])     # Weniger strenge Sättigung
    upper_red1 = np.array([15, 255, 255])  # Größerer Farbbereich
    lower_red2 = np.array([160, 50, 50])   # Weniger strenge Sättigung
    upper_red2 = np.array([180, 255, 255])
    
    # Zusätzlicher Bereich für dunklere Rottöne
    lower_red3 = np.array([0, 50, 20])     # Niedrigere Helligkeit
    upper_red3 = np.array([15, 255, 200])
    
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask3 = cv2.inRange(hsv, lower_red3, upper_red3)
    
    # Kombiniere alle Masken
    mask = cv2.add(cv2.add(mask1, mask2), mask3)
    
    # Verbesserte Rauschreduzierung
    kernel = np.ones((5,5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.medianBlur(mask, 5)  # Zusätzliche Rauschreduzierung
    
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Filtere Konturen nach Größe und Form
    filtered_contours = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > 500:  # Minimale Größe
            # Prüfe Rundheit
            perimeter = cv2.arcLength(cnt, True)
            if perimeter > 0:
                circularity = 4 * np.pi * area / (perimeter * perimeter)
                if circularity > 0.5:  # Schwellenwert für rundliche Objekte
                    filtered_contours.append(cnt)
    
    return filtered_contours

def load_and_preprocess_for_model(image):
    """Prepare image for model prediction"""
    processed = cv2.resize(image, (224, 224))
    processed = processed / 255.0
    processed = np.expand_dims(processed, axis=0)
    return processed

def load_tflite_model(model_path):
    """Load and prepare TFLite model"""
    interpreter = tflite.Interpreter(model_path=model_path)
    interpreter.allocate_tensors()
    return interpreter

def predict_with_tflite(interpreter, input_data):
    """Make prediction using TFLite model"""
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    
    interpreter.set_tensor(input_details[0]['index'], input_data)
    interpreter.invoke()
    
    return interpreter.get_tensor(output_details[0]['index'])[0]

def analyze_image(image, interpreter):
    """Analyze image using the TFLite model"""
    image = adjust_image(image)  # Bild vor der Analyse anpassen
    marked_image = image.copy()
    tomato_contours = detect_tomatoes(image)
    
    results = []
    for contour in tomato_contours:
        x, y, w, h = cv2.boundingRect(contour)
        # Erweitere ROI um 10% für besseren Kontext
        x_ext = max(0, int(x - 0.1 * w))
        y_ext = max(0, int(y - 0.1 * h))
        w_ext = min(image.shape[1] - x_ext, int(1.2 * w))
        h_ext = min(image.shape[0] - y_ext, int(1.2 * h))
        
        tomato_roi = image[y_ext:y_ext+h_ext, x_ext:x_ext+w_ext]
        processed_roi = load_and_preprocess_for_model(tomato_roi)
        
        # Convert to float32 for TFLite
        processed_roi = processed_roi.astype(np.float32)
        
        # Get prediction using TFLite
        prediction = predict_with_tflite(interpreter, processed_roi)[0]
        
        label = "Reif" if prediction > 0.5 else "Unreif"
        color = (0, 255, 0) if prediction > 0.5 else (0, 0, 255)
        confidence = prediction if prediction > 0.5 else 1 - prediction
        
        # Zeichne das Original-Rechteck
        cv2.rectangle(marked_image, (x, y), (x + w, y + h), color, 2)
        label_text = f"{label} ({confidence*100:.1f}%)"
        cv2.putText(marked_image, label_text, (x, y-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
        
        results.append({
            'label': label,
            'confidence': confidence,
            'position': (x, y, w, h)
        })
    
    return marked_image, results

def stream(minutes: int, interpreter):
    """Stream analyzed images to Cumulocity IoT"""
    timeout_timestamp = datetime.datetime.now() + datetime.timedelta(minutes=minutes)

    while datetime.datetime.now() < timeout_timestamp:
        startframetime = datetime.datetime.now()

        id = get_image_id()
        print(f"binary id read: {id}")

        if not id:
            raise Exception(f"No file of type {TYPE} and name {IMAGE_NAME} that can be updated")

        camera = iio.get_reader("<video0>")
        image = camera.get_data(0)
        camera.close()
        
        image_cv2 = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        marked_image, results = analyze_image(image_cv2, interpreter)
        
        cv2.imwrite(IMAGE_PATH, marked_image)  # Verwende cv2.imwrite statt iio.imwrite

        url = f"{C8Y_BASEURL}/inventory/binaries/{id}"
        headers = {"Content-Type": TYPE}
        payload = open(IMAGE_PATH, "rb")

        response = requests.request(
            "PUT", url, headers=headers, data=payload, auth=(USERNAME, PASSWORD)
        )

        time.sleep(1 / FPS - ((datetime.datetime.now() - startframetime).seconds))

if __name__ == "__main__":
    try:
        print(f"Loading model from: {MODEL_PATH}")
        interpreter = load_tflite_model(MODEL_PATH)
        print("Model loaded successfully")

        device_id = sys.argv[1].split(",")[2]
        timeout_minutes = int(sys.argv[1].split(",")[3])

        stream(timeout_minutes, interpreter)

    except Exception as e:
        print(e)
        traceback.print_exc()
