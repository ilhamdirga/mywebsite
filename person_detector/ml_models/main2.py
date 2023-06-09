from mtcnn import MTCNN
import cv2
import os
from keras_facenet import FaceNet
import tensorflow as tf
import numpy as np
from PIL import Image
from numpy import asarray
from django.conf import settings
import pickle
from django.utils import timezone
import time
from person_detector.models import DetectedFace, IpCamera
from django.shortcuts import get_object_or_404
from storages.backends.gcloud import GoogleCloudStorage

import paho.mqtt.client as mqtt
import json

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


my_facenet = FaceNet()

# Di Google Cloud Storage
def make_database_should_crop():
    # Membuat objek GoogleCloudStorage
    storage = GoogleCloudStorage()

    # Mendapatkan nama bucket dari settings.py
    bucket_name = settings.GS_BUCKET_NAME

    # Mendapatkan nama folder
    folder_name = 'person_detector/'

    # Mendapatkan daftar objek dalam folder 'person_detector'
    blobs = storage.listdir(folder_name)[1]

    database = {}
    detector = MTCNN()

    for blob in blobs:
        # Mendapatkan nama file
        filename = os.path.basename(blob)

        # Mendapatkan path file di Google Cloud Storage
        blob_path = os.path.join(folder_name, filename)

        # Membaca konten file dari Google Cloud Storage
        content = storage.open(blob_path).read()

        # Mengubah konten ke gambar menggunakan OpenCV
        nparr = np.frombuffer(content, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Deteksi wajah dan lakukan cropping
        posisi = detector.detect_faces(img)
        x1, y1, w, h = posisi[0]['box']
        x2, y2 = x1 + w, y1 + h
        img_cropped = img[y1:y2, x1:x2]

        # Resize gambar menggunakan PIL
        img_resized = Image.fromarray(img_cropped)
        img_resized = img_resized.resize((160, 160))

        # Konversi gambar menjadi array
        img_array = np.asarray(img_resized)

        # Ekstraksi fitur menggunakan my_facenet.embeddings (perlu didefinisikan)
        embeddings = my_facenet.embeddings(np.expand_dims(img_array, axis=0))[0]

        # Menambahkan gambar dan fitur ke database
        database[filename.split('.')[0]] = embeddings

    return database


def simpan_database(database):
    myfile = open("data.pkl", "wb")
    pickle.dump(database, myfile)
    myfile.close()

def cos_similarity(anchor, test):
    a = np.matmul(np.transpose(anchor), test)
    b = np.sum(np.multiply(anchor, test))
    c = np.sum(np.multiply(test, test))
    return 1 - (a / (np.sqrt(b) * np.sqrt(c)))


def open_camera():
    database = make_database_should_crop()
    simpan_database(database)

    pickle_file = os.path.join(settings.BASE_DIR, 'person_detector', 'ml_models', 'data.pkl')
    with open(pickle_file, 'wb') as myfile:
        pickle.dump(database, myfile)

    haarscascade_path = os.path.join(settings.BASE_DIR, 'person_detector', 'ml_models', 'haarcascade.xml')
    detector = cv2.CascadeClassifier(haarscascade_path)

    last_print_time = time.time()

    camera = IpCamera.objects.latest()
    address = camera.ip_camera
    vid = cv2.VideoCapture(address)

    while(True):
        ret, frame = vid.read()
        wajah = detector.detectMultiScale(frame, scaleFactor = 1.2, minNeighbors = 5)
        if wajah is not None:
            for x1, y1, w, h in wajah:
                x2 = x1 + w
                y2 = y1 + h
                muka = frame[y1:y2, x1:x2]
                muka = cv2.cvtColor(muka, cv2.COLOR_BGR2RGB)
                muka = Image.fromarray(muka)
                muka = muka.resize((160,160)) 
                muka = asarray(muka)
                muka = np.expand_dims(muka, axis=0)
                test_embedder = my_facenet.embeddings(muka)[0]
                i = 100
                k = 'Unknown'
                
                for key in database:
                    distance = cos_similarity(database.get(key), test_embedder)
                    if (distance < i) & (distance < 0.5):
                        i = distance
                        k = key
                
                if k:
                    current_time = timezone.now()
                    if time.time() - last_print_time >= 1:
                        detected_face = DetectedFace.objects.create(name=k, detected_time=current_time)
                        detected_face.save()
                        last_print_time = time.time()  # Memperbarui waktu terakhir pesan dicetak dan data disimpan
                            
                        formatted_time = current_time.strftime('%d%m%Y')
                        pesan = {
                            'name': k,
                            'timestamp': formatted_time
                        }
                        send_message_to_mqtt(pesan)

                        print(f"Nama wajah terdeteksi: {k}; Waktu: {current_time}")
                    


                frame = cv2.rectangle(frame, (x1,y1), (x2,y2), (255,255,255), 1)
                frame = cv2.putText(frame, k, (x1,y1), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
                cv2.imshow('frame', frame)
            
        key = cv2.waitKey(2)
        if key == 27:  # Tombol Esc
            break

    
    vid.release()
    cv2.destroyAllWindows()