from flask import Flask, render_template, request, redirect, url_for, jsonify
from dotenv import load_dotenv
import requests
from supabase import create_client
import os
import cv2
import numpy as np
import pickle

with open("labels.pkl", "rb") as f:
    label_map = pickle.load(f)

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)
def get_recognized_name():

    import pickle
    import cv2

    with open("labels.pkl", "rb") as f:
        label_map = pickle.load(f)

    img = cv2.imread("static/captured_student.jpg")

    if img is None:
        return "Unknown"

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    if len(faces) == 0:
        return "Unknown"

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read("trainer.yml")

    (x, y, w, h) = faces[0]
    face = gray[y:y+h, x:x+w]

    label, confidence = recognizer.predict(face)

    return label_map.get(label, "Unknown")

@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        result = (
            supabase.table("admins")
            .select("*")
            .eq("username", username)
            .eq("password_hash", password)
            .execute()
        )

        if result.data:
            return redirect(url_for("dashboard"))

        return render_template(
            "login.html",
            error="Invalid username or password"
        )

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")
@app.route("/students")
def students():

    response = supabase.table("students").select("*").execute()

    return render_template(
        "students.html",
        students=response.data
    )
@app.route("/monitoring", methods=["GET", "POST"])
def monitoring():

    students = supabase.table("students").select("*").execute()
    message = None

    if request.method == "POST":

        import requests

        response = requests.post("http://127.0.0.1:5000/recognize")
        data = response.json()

        recognized_name = data.get("name", "Unknown")

        student_id = request.form["student_id"]
        event_type = request.form["event_type"]

        student_result = (
            supabase.table("students")
            .select("*")
            .eq("id", student_id)
            .execute()
        )

        student = student_result.data[0]

        # Attendance
        supabase.table("attendance").insert({
    "student_id": student_id,
    "student_no": student["student_no"],   # ⭐ ADD THIS
    "event_type": event_type,
    "recognition_confidence": 98
}).execute()
        # Event Log
        supabase.table("event_logs").insert({
    "student_id": student_id,
    "student_name": student["student_name"],
    "student_no": student["student_no"],   # ⭐ ADD THIS
    "event_type": event_type,
    "notification_sent": True
}).execute()()

        message = (
            f"Notification Sent ✓ Dear Parent, your child "
            f"{student['student_name']} {event_type.lower()}ed the campus."
        )

    return render_template(
        "monitoring.html",
        students=students.data,
        message=message
    )
@app.route("/capture")
def capture():

    import os

    os.system("python3 camera.py")

    # STEP 1: recognize immediately
    name = get_recognized_name()

    # STEP 2: push to database instantly
    supabase.table("event_logs").insert({
        "student_name": name,
        "event_type": "Entry",
        "notification_sent": True
    }).execute()

    return redirect(url_for("monitoring"))
import cv2
import numpy as np

recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read("trainer.yml")

@app.route("/recognize", methods=["POST"])
def recognize():

    img = cv2.imread("static/captured_student.jpg")

    if img is None:
        return {"name": "No Image"}

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    if len(faces) == 0:
        return {"name": "No Face Detected"}

    (x, y, w, h) = faces[0]
    face = gray[y:y+h, x:x+w]

    label, confidence = recognizer.predict(face)

    name = label_map.get(label, "Unknown")

    return {"name": name}
@app.route("/attendance")
def attendance():
    response = supabase.table("attendance").select("*").execute()
    return render_template("attendance.html", logs=response.data)
@app.route("/eventlogs")
def eventlogs():
    response = supabase.table("event_logs").select("*").order("id", desc=True).execute()
    return render_template("eventlogs.html", logs=response.data)
@app.route("/alerts")
def alerts():
    return render_template("alerts.html")

     
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)