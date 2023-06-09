import cv2
import os
import pickle
from datetime import datetime
from django.utils import timezone
import time
import paho.mqtt.client as mqtt
import json
import io

from django.conf import settings
from trash_can_detector.models import Gallery, Camera, CamCard
from django.shortcuts import get_object_or_404
from django.contrib import messages
from tensorflow.keras.models import load_model
from tensorflow.keras.utils import load_img, img_to_array
import numpy as np
from storages.backends.gcloud import GoogleCloudStorage
from django.core.files.base import ContentFile


# Konfigurasi MQTT
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker")
    else:
        print("Failed to connect, return code %d" % rc)

def on_publish(client, userdata, mid):
    print("Message successfully published")

def on_disconnect(client, userdata, rc):
    print("Disconnected from MQTT Broker")

def connect_mqtt():
    client = mqtt.Client()
    client.username_pw_set("ea64a3ae-b6fb-4ffa-934c-017f22928eb5", "i5G0SWEn0r3FhDxVEYvoQKDLd9KnRjlT9YDABvVCuZtSTpZJfrxRaR68hGKcYqlrp5rTpumrxwttqlxz")  # Ganti dengan nama pengguna dan kata sandi yang sesuai
    client.on_connect = on_connect
    client.on_publish = on_publish
    client.on_disconnect = on_disconnect

    # Ganti dengan alamat dan port broker MQTT yang sesuai
    broker_address = "telemetry.iotstadium.com"
    port = 1883

    try:
        client.connect(broker_address, port)
        client.loop_start()
        return client
    except Exception as e:
        print("Error connecting to MQTT Broker:", str(e))
        return None

def send_mqtt_message(client, topic, message):
    try:
        json_message = json.dumps(message)
        result, mid = client.publish(topic, json_message)
        if result == mqtt.MQTT_ERR_SUCCESS:
            print('Message successfully sent')
        else:
            print('Failed to send message, return code %d' % result)
    except Exception as e:
        print("Error sending MQTT message:", str(e))

def disconnect_mqtt(client):
    client.loop_stop()
    client.disconnect()

def send_message_to_mqtt(pesan):
    client = connect_mqtt()
    if client:
        topic = 'ea64a3ae-b6fb-4ffa-934c-017f22928eb5'
        message = pesan
        send_mqtt_message(client, topic, message)
        disconnect_mqtt(client)
# Akhir Konfigurasi

# Count status trash-can
def loadModel(path_model):
    return load_model(path_model)

def prediksi(model, tes_path):
    img = load_img(tes_path, target_size=(150, 150))
    x = img_to_array(img)
    x /= 255
    x = np.expand_dims(x, axis=0)
    images = np.vstack([x])
    predict = model.predict(images)
    if predict[0][0] >= 0.5:
        return 1
    return 0

def open_camera(cam_id):
    # Mengambil instance camera sesuai Camera ID
    camera = get_object_or_404(Camera, id=cam_id)
    address = camera.ip_camera
    cam = cv2.VideoCapture(address)
    # cam.open(address)

    # Cek apakah file counter sudah ada
    counter_file = os.path.join(settings.BASE_DIR, 'trash_can_detector', 'ml_models', 'counter.pkl')
    if os.path.exists(counter_file):
        with open(counter_file, 'rb') as f:
            photo_counter = pickle.load(f)
    else:
        photo_counter = 1

    show_text = False
    text_timer = 0
    display_time = 2

    
    while True:
        check, frame = cam.read()

         # Menambahkan teks ke frame
        if show_text:
            text = f'Photo {camera.name} saved!'
            cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            if time.time() - text_timer > display_time:
                show_text = False

        cv2.imshow(f'{camera.name}', frame)
        key = cv2.waitKey(1)

        if key == 32:           

            # Generate photo name
            photo_name = f'{camera.name}-{photo_counter}.jpg'
 
            picture = cv2.imencode('.jpg', frame)[1].tostring()

            # Mengunggah file ke Google Cloud Storage
            gcs = GoogleCloudStorage()
            file_name = f'{camera.name}-{photo_counter}.jpg'
            file_path = f'trash_can_detector/{file_name}'  # Nama direktori di google cloud storage
            content_file = io.BytesIO(picture)
            gcs.save(file_path, content_file)

            # Menghitung prediksi dengan menggunakan model
            path_model = os.path.join(settings.BASE_DIR, 'trash_can_detector', 'ml_models', 'newest_model.h5')
            model = load_model(path_model)
            result = prediksi(model, content_file)

            if result == 0:
                capacity = 'Not Full'
            else:
                capacity = 'Full'

            current_time = timezone.now()
            gallery = Gallery.objects.create(name = camera,
                                             picture = file_path, 
                                             capacity = capacity,
                                             timestamp = current_time
                                             )
            gallery.save()
            
            formatted_time = current_time.strftime('%d%m%Y')
            message = {
                    'name': camera.name,
                    'capacity': str(result),
                    'timestamp': formatted_time
                    }
            send_message_to_mqtt(message)

            photo_counter += 1
            print(f'Photo {photo_name} saved!')

            # Menampilkan teks selama 3 detik
            show_text = True
            text_timer = time.time()

        elif key == 27:
            break

    cam.release()
    cv2.destroyAllWindows()

    # Simpan nilai counter ke dalam file
    with open(counter_file, 'wb') as f:
        pickle.dump(photo_counter, f)