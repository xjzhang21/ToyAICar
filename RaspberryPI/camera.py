import numpy as np
import zmq
import cv2

context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.setsockopt(zmq.CONFLATE, 1)
socket.bind("tcp://*:5555")

print('START')

cap1 = cv2.VideoCapture(0)
cap1.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cap1.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
cap1.set(cv2.CAP_PROP_FPS, 30)

cap2 = cv2.VideoCapture(1)
cap2.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cap2.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
cap2.set(cv2.CAP_PROP_FPS, 30)

num_frame = 0
while True:
    cap1.grab()
    cap2.grab()

    if num_frame % 3 == 0:
        ret, frame1 = cap1.retrieve()
        ret, frame2 = cap2.retrieve()
        
        frame = np.concatenate([frame1, frame2], 1)
        
        n = frame.size
        ret, frame = cv2.imencode('.jpg', frame, (cv2.IMWRITE_JPEG_QUALITY, 20))
        n2 = frame.size
        
        socket.send_pyobj(frame)
        print('frame %d, compress ratio %f' % (i, n2 / n))

    num_frame += 1