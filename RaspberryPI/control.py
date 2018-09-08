import numpy as np
import zmq
import serial

context = zmq.Context()
control_socket = context.socket(zmq.SUB)
control_socket.setsockopt(zmq.CONFLATE, 1)
control_socket.connect('tcp://192.168.0.100:6666')
control_socket.setsockopt(zmq.SUBSCRIBE, b'')

port = serial.Serial('/dev/ttyUSB0', 9600, timeout = 1)

while True:
    control_data = control_socket.recv_pyobj()
    steering = control_data['steering']
    velocity = control_data['velocity']
    
    port.write(b'S %f\n' % steering)
    port.write(b'V %f\n' % velocity)

    print('steering:', steering, 'velocity:', velocity)
    