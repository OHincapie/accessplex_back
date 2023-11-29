from flask import Flask, render_template, Response
import cv2
import numpy as np
import mediapipe as mp
from bs4 import BeautifulSoup
from flask import request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)
camera = cv2.VideoCapture(0)
face_mesh = mp.solutions.face_mesh.FaceMesh(refine_landmarks=True)
face_detection = mp.solutions.face_detection.FaceDetection()
mp_drawing = mp.solutions.drawing_utils
camera_width, camera_height = 250, 150
circle_radius = 5
circle_color = (0, 255, 0)

l_eye_x = 0
l_eye_y = 0
r_eye_x = 0
r_eye_y = 0

square_x = 300
square_y = 200
square_size = 200

rectangle_x = square_x + 50
rectangle_y = square_y + 50
rectangle_width = 100
rectangle_height = 100

width = 0
height = 0



@app.route('/')
def index():
    return render_template('index.html')

def generate_frames():
    global original_x
    global original_y
    global click
    desired_x = 150
    desired_y = 200
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            frame = cv2.flip(frame, 1)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # Calcular las coordenadas de recorte
            start_y = (frame.shape[0] - desired_y) // 2
            end_y = start_y + desired_y
            start_x = (frame.shape[1] - desired_x) // 2
            end_x = start_x + desired_x
            # Recortar la imagen
            frame_mesh = frame.copy()[start_y:end_y, start_x:end_x]
            results = face_mesh.process(frame_mesh)
            frame_detection = frame
            results_face = face_detection.process(frame_detection)
            if results_face.detections:
                for detection in results_face.detections:
                    mp_drawing.draw_detection(frame, detection)
            # print((frame.shape[1] - end_x, frame.shape[0] - end_y), (frame.shape[1] - start_x, frame.shape[0] - start_y))
            # frame = cv2.rectangle(frame, pt1=(220, 140), pt2=(420, 340), color=(255, 0, 0) , thickness=2) 
            frame = cv2.rectangle(frame, pt1=(frame.shape[1] - end_x, frame.shape[0] - end_y), pt2=(frame.shape[1] - start_x, frame.shape[0] - start_y), color=(255, 0, 0) , thickness=2) 
            frame = cv2.resize(frame, (camera_width, camera_height))

            if results.multi_face_landmarks:
                
                face_landmarks = results.multi_face_landmarks[0]
                original_x = float(face_landmarks.landmark[168].x)
                original_y = float(face_landmarks.landmark[168].y)
                left = [face_landmarks.landmark[145], face_landmarks.landmark[159]]
                rigth = [face_landmarks.landmark[374], face_landmarks.landmark[386]]
                
                if (left[0].y - left[1].y) < 0.02 or (rigth[0].y - rigth[1].y) < 0.02:
                    click = True
                else:
                    click = False
                # print(frame.shape[1])
            #     x = int(face_landmarks.landmark[4].x * (start_x +end_y) //2)
            #     y = int(face_landmarks.landmark[4].y * 200)
            #     print((x,y))
            #     # Ojo izquierdo
            #     l_eye = face_landmarks.landmark[33]
            #     l_eye_x = int(l_eye.x * frame.shape[1])
            #     l_eye_y = int(l_eye.y * frame.shape[0])

            #     # Ojo derecho
            #     r_eye = face_landmarks.landmark[263]
            #     r_eye_x = int(r_eye.x * frame.shape[1])
            #     r_eye_y = int(r_eye.y * frame.shape[0])

            
            # frame = cv2.circle(frame, (x, y), circle_radius, circle_color, -1)
            # # Voltear horizontalmente para sincronizar
            # frame = cv2.circle(frame, (l_eye_x, l_eye_y), 3, (0, 255, 255), 5)
            # frame = cv2.circle(frame, (r_eye_x, r_eye_y), 3, (0, 0, 255), 5)
            #En vez de numero quemados debo de poner las dimensiones de mi div interaccion
            circle_x1 = (l_eye_x /frame.shape[1]) * 1000 
            circle_y1 = (l_eye_y /frame.shape[0]) *700
            circle_x2 = (r_eye_x /frame.shape[1]) * 1000
            circle_y2 = (r_eye_y /frame.shape[0]) *700
            
            _, buffer = cv2.imencode('.jpg', cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            
@socketio.on('eye_movement')         
def eye_movement(data):
    emit('test', {'x': width_screen * original_x , 'y': height_screen * original_y}, broadcast=True)

@socketio.on('eye_click')         
def eye_click(data):
    global click
    if data:
        click = False
        
    emit('click', click, broadcast=True)

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/dimension', methods=['POST'])
def dimension():
    global width_screen, height_screen
    width_screen = float(request.form['width'])
    height_screen = float(request.form['height']) - (camera_height + 10)
    print(type(width_screen))
    print(width_screen)
    return 'Ancho del div recibido correctamente'

if __name__ == "__main__":
    app.run(debug=True)
