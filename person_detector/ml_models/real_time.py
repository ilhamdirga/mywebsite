from mtcnn import MTCNN
import cv2
import os
from keras_facenet import FaceNet
import tensorflow as tf
import numpy as np
from PIL import Image
from numpy import asarray
import pickle

def cos_similarity(anchor, test):
    a = np.matmul(np.transpose(anchor), test)
    b = np.sum(np.multiply(anchor, test))
    c = np.sum(np.multiply(test, test))
    return 1 - (a / (np.sqrt(b) * np.sqrt(c)))

detector = cv2.CascadeClassifier('haarcascade.xml')

file = open('data.pkl', 'rb')
database = pickle.load(file)
file.close()

vid = cv2.VideoCapture(0)
while(True):
    ret, frame = vid.read()
    wajah = detector.detectMultiScale(frame, scaleFactor = 1.2, minNeighbors = 5)
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
        k = 'unknown'
        for key in database:
            distance = cos_similarity(database.get(key), test_embedder)
            if (distance < i) & (distance < 0.5):
                i = distance
                k = key
        frame = cv2.rectangle(frame, (x1,y1), (x2,y2), (255,255,255), 1)
        frame = cv2.putText(frame, k, (x1,y1), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
        cv2.imshow('frame', frame)
    
        if cv2.waitKey(2) & 0xFF == ord('q'):
            break
  
    vid.release()
    cv2.destroyAllWindows()