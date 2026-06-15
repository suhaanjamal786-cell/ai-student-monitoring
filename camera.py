import cv2

camera = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)

while True:
    success, frame = camera.read()

    if not success:
        break

    cv2.imshow("AI Student Safety Monitoring", frame)

    key = cv2.waitKey(1)

    # Press SPACE to capture
    if key % 256 == 32:
        cv2.imwrite("static/captured_student.jpg", frame)
        import requests

        response = requests.post("http://127.0.0.1:5000/recognize")
        print(response.json())
        print("Photo captured!")
        break

    # Press ESC to exit
    elif key % 256 == 27:
        break

camera.release()
cv2.destroyAllWindows()