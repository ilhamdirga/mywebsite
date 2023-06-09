import cv2
import numpy as np
from tensorflow.keras.layers import Input, Lambda, Dense
from tensorflow.keras.models import load_model, Model
import os
from . import utils
from .siamese_network import buat_siamese
from . import config
from django.utils import timezone

import datetime
import time

from django.conf import settings
from person_detector.models import DetectedFace, IpCamera
from django.shortcuts import get_object_or_404

import paho.mqtt.client as mqtt
import json

haarscascade_path = os.path.join(settings.BASE_DIR, 'person_detector', 'ml_models', 'haarcascade.xml')
detector = cv2.CascadeClassifier(haarscascade_path)

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
    client.username_pw_set("87f91c55-b35f-46dc-b876-60606d526e4a", "M44o0Tz3DotSYbOQuIfOvwVlhVgVz0BDQcg4kTKeAQMUtAHzC4h6kdki7RkpeUBzWH5xjW7rmPYeDUCc")  # Ganti dengan nama pengguna dan kata sandi yang sesuai
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
        topic = '87f91c55-b35f-46dc-b876-60606d526e4a'
        message = pesan
        send_mqtt_message(client, topic, message)
        disconnect_mqtt(client)
# Akhir Konfigurasi

def open_camera():

    def model():
        inpA = Input(config.img_shape)
        inpB = Input(config.img_shape)

        embedder = buat_siamese(config.img_shape)
        vectorA = embedder(inpA)
        vectorB = embedder(inpB)

        dist = Lambda(utils.distance)([vectorA, vectorB])
        outputs = Dense(1, activation="sigmoid")(dist)
        return Model(inputs=[inpA, inpB], outputs=outputs)

    def prediksi_muka(frame, model):
        hasil = []
        label = []
        for data in database:
            img = database[data]
            tes = (frame, img)
            tes = np.array([tes])
            tes = np.expand_dims(tes, axis=-1)
            tmp = model.predict([tes[:,0,:], tes[:,1,:]])
            hasil.append(tmp)
            label.append(data)
        return hasil, label

    def hasil_prediksi(hasil, label):
        maks = max(hasil)
        indeks = hasil.index(maks)
        if maks > 0.2:
            teks = label[indeks]
        else:
            teks = 'Unknown'
        return teks

    def buat_database():
        database_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'person_detector')
        images = os.listdir(database_path)
        database = {}
        for image in images:
            path = os.path.join(database_path, image)
            img = cv2.imread(path, 0)
            img = cv2.resize(img, (105,105), interpolation=cv2.INTER_AREA)/255.
            database[image.split('.')[0]] = img
        return database




    new_model = model()
    file_path = os.path.join(settings.BASE_DIR, 'person_detector', 'ml_models', 'siamese_weights.h5')
    new_model.load_weights(file_path)
    database = buat_database()

    
    camera = IpCamera.objects.latest()
    address = camera.ip_camera
    cam = cv2.VideoCapture(0)
    # vid.open(address)

    last_print_time = time.time()
    teks = ''  # Inisialisasi variabel 'teks'
    # success = True
    # error = None
    while(True):
        check, frame = cam.read()

        wajah = detector.detectMultiScale(frame, scaleFactor = 1.2, minNeighbors = 5)
        if wajah is not None:  # Tambahkan pengecekan None
            for x1, y1, w, h in wajah:
                x2 = x1 + w
                y2 = y1 + h
                muka = frame[y1:y2, x1:x2]
                muka = cv2.cvtColor(muka, cv2.COLOR_BGR2GRAY)
                muka = cv2.resize(muka, (105,105), interpolation=cv2.INTER_AREA)/255.
                hasil, label = prediksi_muka(muka, new_model)
                teks = hasil_prediksi(hasil, label)

                if teks:
                    current_time = timezone.now()
                    if time.time() - last_print_time >= 0.5:
                        detected_face = DetectedFace.objects.create(name=teks, detected_time=current_time)
                        detected_face.save()
                        last_print_time = time.time()  # Memperbarui waktu terakhir pesan dicetak dan data disimpan
                            
                        formatted_time = current_time.strftime('%d%m%Y')
                        pesan = {
                            'name': teks,
                            'timestamp': formatted_time
                        }
                        send_message_to_mqtt(pesan)

                        print(f"Nama wajah terdeteksi: {teks}; Waktu: {current_time}")

                frame = cv2.rectangle(frame, (x1,y1), (x2,y2), (255,255,255), 1)
                frame = cv2.putText(frame, teks, (x1,y1), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
                cv2.imshow('frame', frame)
        
        # print(f'terdeteksi: {teks}')
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    

    cam.release()

    cv2.destroyAllWindows()

    # return success, error