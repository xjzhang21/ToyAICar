import numpy as np
import matplotlib.pyplot as plt
import cv2
import zmq

context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.setsockopt(zmq.CONFLATE, 1)
socket.connect('tcp://192.168.0.105:5555')
socket.setsockopt(zmq.SUBSCRIBE, b'')

left_targets = np.array([[-110, 120], [-90, 120], [-70, 120], [-50, 120],
                         [-110, 100], [-90, 100], [-70, 100], [-50, 100],
                         [-110, 80], [-90, 80], [-70, 80], [-50, 80]]).reshape([-1, 1, 2])
right_targets = np.array([[50, 120], [70, 120], [90, 120], [110, 120],
                          [50, 100], [70, 100], [90, 100], [110, 100],
                          [50, 80], [70, 80], [90, 80], [110, 80]]).reshape([-1, 1, 2])

left_targets[:, :, 0] += 320
right_targets[:, :, 0] += 320

while True:
    frame = socket.recv_pyobj()
    frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)

    left_frame = frame[:, 0:320]
    right_frame = frame[:, 320:]

    # Gray
    right_gray = cv2.cvtColor(right_frame, cv2.COLOR_BGR2GRAY)
    left_gray = cv2.cvtColor(left_frame, cv2.COLOR_BGR2GRAY)

    # Find chessboard
    left_ret, left_corners = cv2.findChessboardCorners(left_gray, (4, 3), None)
    right_ret, right_corners = cv2.findChessboardCorners(right_gray, (4, 3), None)
    cv2.drawChessboardCorners(left_frame, (4, 3), left_corners, left_ret)
    cv2.drawChessboardCorners(right_frame, (4, 3), right_corners, right_ret)

    # Homography
    if left_ret and right_ret:
        left_h, mask_left = cv2.findHomography(left_corners, left_targets)
        right_h, mask_right = cv2.findHomography(right_corners, right_targets)

        np.save('left_h.npy', left_h)
        np.save('right_h.npy', right_h)

        # perspectiveTransform to world coordinates
        left_dest = cv2.perspectiveTransform(left_corners, left_h)
        right_dest = cv2.perspectiveTransform(right_corners, right_h)

        plt.clf()
        plt.scatter(left_dest[:, :, 0], left_dest[:, :, 1], c='r')
        plt.scatter(right_dest[:, :, 0], right_dest[:, :, 1], c='b')
        plt.xlim([0, 640])
        plt.ylim([0, 480])
        plt.grid()
        plt.pause(0.001)

    cv2.imshow('left', left_frame)
    cv2.imshow('right', right_frame)
    cv2.waitKey(1)
