import cv2
import os
import io
import pickle
from datetime import datetime
import time
import paho.mqtt.client as mqtt
import json
import socket

from django.contrib import messages
from django.shortcuts import redirect
from django.utils import timezone
from tensorflow.keras.models import load_model
from tensorflow.keras.utils import load_img, img_to_array
import numpy as np 

from django.conf import settings
from memory_tray_detector.models import Gallery, Camera, CamCard
from django.shortcuts import get_object_or_404
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
    client.username_pw_set("f4211843-ae3c-4e5d-9f3a-87c27aec1066", "ltvxkTFHRBv8Hcg2RNHpkivLzox3z4b0XtBBLSLH3ZP9fY9w2D7l59Kcg5IRiP1qxgLD4nVsNCU2mEN2")  # Ganti dengan nama pengguna dan kata sandi yang sesuai
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
        topic = 'f4211843-ae3c-4e5d-9f3a-87c27aec1066'
        message = pesan
        send_mqtt_message(client, topic, message)
        disconnect_mqtt(client)
# Akhir Konfigurasi


# Count remaining-quantity mtray ssd
def buat_model(path_model):
    return load_model(path_model)

def predict_ssd(tes_path, model):
    img = load_img(tes_path, target_size=(300, 300))
    x = img_to_array(img)
    x /= 255
    x = np.expand_dims(x, axis=0)
    images = np.vstack([x])
    yhat = model.predict(images)
    yhat = np.argmax(yhat, axis=1)[0]
    return yhat

def open_camera(cam_id):
        # Mengambil instance camera sesuai Camera ID
        camera = get_object_or_404(Camera, id=cam_id)
        address = camera.ip_camera
        cam = cv2.VideoCapture(address)

        # Cek apakah file counter sudah ada
        counter_file = os.path.join(settings.BASE_DIR, 'memory_tray_detector', 'ml_models', 'counter.pkl')
        if os.path.exists(counter_file):
            with open(counter_file, 'rb') as f:
                photo_counter = pickle.load(f)
        else:
            photo_counter = 1

        show_text = False
        text_timer = 0
        display_time = 0.5

        
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
                file_path = f'memory_tray_detector/{file_name}'  # Nama Direktori di google cloud storage
                content_file = io.BytesIO(picture)
                gcs.save(file_path, content_file)

                # Menghitung remaining capacity ssd
                path_model = os.path.join(settings.BASE_DIR, 'memory_tray_detector', 'ml_models', 'model_SSD.h5')
                model = buat_model(path_model)
                result = predict_ssd(content_file, model)

                # Simpan photo ke models Gallery
                quantity = result
                type_tray = 'SSD'

                current_time = timezone.now()
                gallery = Gallery.objects.create(name = camera,
                                                picture = file_path, 
                                                quantity = quantity,
                                                type_tray = type_tray,
                                                timestamp = current_time
                                                )
                gallery.save()

                formatted_time = current_time.strftime('%d%m%Y')
                message = {
                        'name': camera.name,
                        'remaining-quantity': str(quantity),
                        'type': type_tray,
                        'timestamp': formatted_time
                    }
                send_message_to_mqtt(message)

                photo_counter += 1
                print(f'Photo {photo_name} saved!')

                show_text = True
                text_timer = time.time()

            elif key == 27:
                break

        cam.release()
        cv2.destroyAllWindows()

        # Simpan nilai counter ke dalam file
        with open(counter_file, 'wb') as f:
            pickle.dump(photo_counter, f)
