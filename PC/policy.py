import numpy as np
import zmq
import cv2

context = zmq.Context()
camera_socket = context.socket(zmq.SUB)
camera_socket.setsockopt(zmq.CONFLATE, 1)
camera_socket.connect('tcp://192.168.0.105:5555')
camera_socket.setsockopt(zmq.SUBSCRIBE, b'')

control_socket = context.socket(zmq.PUB)
control_socket.setsockopt(zmq.CONFLATE, 1)
control_socket.bind('tcp://*:6666')

LEFT_H = np.load('left_h.npy')
RIGHT_H = np.load('right_h.npy')

LANE_WIDTH = 390

while True:
    frame = camera_socket.recv_pyobj()
    frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)

    # Split left and right views
    left_img = frame[:, 0:320]
    right_img = frame[:, 320:]
    cv2.imshow('left_img', left_img)
    cv2.imshow('right_img', right_img)

    # Gray left and right
    gray = cv2.cvtColor(left_img, cv2.COLOR_BGR2GRAY)
    thres, left_binary = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY_INV)

    gray = cv2.cvtColor(right_img, cv2.COLOR_BGR2GRAY)
    thres, right_binary = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY_INV)
    # cv2.imshow('bin',left_binary)

    # Perspective in the real world
    left_pers = cv2.warpPerspective(left_binary, LEFT_H, (640, 320))
    right_pers = cv2.warpPerspective(right_binary, RIGHT_H, (640, 320))
    top_full_pers = left_pers + right_pers
    top_full_pers_color = cv2.cvtColor(top_full_pers, cv2.COLOR_GRAY2BGR)
    #cv2.imshow('top_full', top_full_pers[::-1])

    # Estimate the initial nearnest search position
    hist = top_full_pers[:150].sum(0)
    left_center = np.argmax(hist[50:320]) + 50
    right_center = np.argmax(hist[320:590]) + 320

    # Segment the left lane points
    left_points_x, left_points_y = np.zeros(0, dtype=int), np.zeros(0, dtype=int)
    if left_center > 50:
        for i in range(0, 320, 32):
            window = top_full_pers[i:i+32, left_center-50: left_center+50]
            if window.sum() > 50*255:
                n = window.sum(0)
                left_center = max(left_center-50+int((np.arange(100)*n).sum()/n.sum()), 50)
                window = top_full_pers[i:i+32, left_center-50: left_center+50]
            y, x = window.nonzero()
            left_points_x = np.concatenate([left_points_x, left_center - 50 + x])
            left_points_y = np.concatenate([left_points_y, y+i])
            cv2.rectangle(top_full_pers_color, (left_center-50, i), (left_center+50, i+32), (0, 0, 90))
    top_full_pers_color[left_points_y, left_points_x] = [0, 0, 128]

    # Segment the right lane points
    right_points_x, right_points_y = np.zeros(0, dtype=int), np.zeros(0, dtype=int)
    if right_center > 320:
        for i in range(0, 320, 32):
            window = top_full_pers[i:i+32, right_center-50: right_center+50]
            if window.sum() > 50*255:
                n = window.sum(0)
                right_center = min(right_center-50+int((np.arange(100)*n).sum()/n.sum()), 640-50)
                window = top_full_pers[i:i+32, right_center-50:right_center+50]
            y, x = window.nonzero()
            right_points_x = np.concatenate([right_points_x, right_center - 50 + x])
            right_points_y = np.concatenate([right_points_y, y+i])
            cv2.rectangle(top_full_pers_color, (right_center-50, i), (right_center+50, i+32), (0, 90, 0))
    top_full_pers_color[right_points_y, right_points_x] = (0, 128, 0)

    # two lanes can be viewed
    if len(left_points_x) > 0 and len(right_points_x) > 0:
        fit_y = np.concatenate([left_points_y, right_points_y])
        fit_x = np.concatenate([left_points_x+LANE_WIDTH//2, right_points_x-LANE_WIDTH//2])
    # only the left lane can be viewed
    elif len(left_points_x) > 0:
        fit_y = left_points_y
        fit_x = left_points_x + LANE_WIDTH//2
    # only the right lane can be viewed
    elif len(right_points_x) > 0:
        fit_y = right_points_y
        fit_x = right_points_x - LANE_WIDTH//2
    else:
        fit_x = fit_y = None

    if fit_x is not None:
        p = np.polyfit(fit_y, fit_x, 2)

        y0 = np.arange(0, 320)
        x0 = np.polyval(p, y0).astype(np.int)
        # left
        y, x = y0, x0 - LANE_WIDTH//2
        t = (x > 0) & (x < 640)
        y, x = y[t], x[t]
        top_full_pers_color[y, x] = (0, 0, 255)
        # right
        y, x = y0, x0 + LANE_WIDTH//2
        t = (x > 0) & (x < 640)
        y, x = y[t], x[t]
        top_full_pers_color[y, x] = (0, 255, 0)

        x = np.polyval(p, 0)
        delta_x = 320 - x
        curvature = 2*p[0]/(1+(2*p[0]*0+p[1])**2)**1.5
        print(delta_x, curvature)

        steering = -0.5 * delta_x
        velocity = 100
        control_data = {'steering': steering, 'velocity': velocity}
        control_socket.send_pyobj(control_data)

    cv2.imshow('top_full', top_full_pers_color[::-1])
    cv2.waitKey(1)
