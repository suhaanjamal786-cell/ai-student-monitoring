import cv2
import os
import numpy as np

recognizer = cv2.face.LBPHFaceRecognizer_create()
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

faces = []
labels = []
label_map = {}

dataset_path = "student_photos"

label_id = 0

for person in os.listdir(dataset_path):

    person_path = os.path.join(dataset_path, person)

    if not os.path.isdir(person_path):
        continue

    label_map[label_id] = person

    for img_name in os.listdir(person_path):

        img_path = os.path.join(person_path, img_name)
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)

        if img is None:
            continue

        gray = img

        faces_detected = face_cascade.detectMultiScale(gray, 1.3, 5)

        if len(faces_detected) == 0:
            continue  # IMPORTANT: skip bad images safely

        for (x, y, w, h) in faces_detected:
             face = gray[y:y+h, x:x+w]
             faces.append(face)
             labels.append(label_id)
            

             label_id += 1

             recognizer.train(faces, np.array(labels))
             recognizer.save("trainer.yml")

             print("Training complete!")
             print(label_map)
import pickle

with open("labels.pkl", "wb") as f:
    pickle.dump(label_map, f)