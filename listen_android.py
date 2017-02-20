# coding=utf-8
# echo_server.py
import socket
import json
import numpy as np
import matplotlib.pyplot as plt
import time
import threading
import Queue
import datetime

class PlotThread(threading.Thread):
    # some X and Y data
    rest = ""
    buffer_size = 1000
    x = np.array([time.time()]*buffer_size,dtype=np.float64)
    y = np.zeros(buffer_size)
    mag_xy_plane = np.zeros(buffer_size)
    mag_xyz = np.zeros((3,buffer_size))
    mag_vec = np.zeros(3)

    def __init__(self, queue):
        self.__queue = queue
        threading.Thread.__init__(self)

    def run(self):
        while 1:
            item = self.__queue.get()
            if item is None:
                break # reached end of queue
            try:
                if self.rest != "":
                    item = self.rest + item
                    self.rest = ""
                vals = json.loads(item)

            except Exception as e:
                #print e, item
                self.rest = item
                continue
            self.mag_vec[0] = vals['Mag_x']
            self.mag_vec[1] = vals['Mag_y']
            self.mag_vec[2] = vals['Mag_z']
            time = vals['date']/1000.0
            strength = np.sqrt((self.mag_vec ** 2).sum())
            x_y_plane= np.sqrt((self.mag_vec[0:2] ** 2).sum())
            self.x[:-1] = self.x[1:]
            self.x[-1:] = time

            x_index = map(datetime.datetime.fromtimestamp,self.x)
            self.y[:-1] = self.y[1:]
            self.y[-1:] = strength

            self.mag_xy_plane[:-1] = self.mag_xy_plane[1:]
            self.mag_xy_plane[-1:] = x_y_plane

            self.mag_xyz[:,:-1] = self.mag_xyz[:,1:]
            self.mag_xyz[:,-1] =self.mag_vec
            # set the new data
            if self.__queue.qsize() > 5:
                continue
            plt.clf()
            plt.plot(x_index, self.y, c='green', label='S')
            plt.plot(x_index, self.mag_xy_plane, c='orange', label='x-y-Plane')
            plt.plot(x_index, self.mag_xyz[0,:], c='blue', label='x')
            plt.plot(x_index, self.mag_xyz[1,:], c='red', label='y')
            plt.plot(x_index, self.mag_xyz[2,:], c='purple', label='z')
            plt.ylabel('Unit ($1e-6 T$)')
            plt.xlabel('Time')
            plt.xticks(rotation=35)
            plt.legend()
            plt.pause(.00001)



if __name__ == '__main__':
    _queue = Queue.Queue()
    host = ''        # Symbolic name meaning all available interfaces
    port = 9999     # Arbitrary non-privileged port
    print socket.gethostbyaddr(socket.gethostname())
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    print socket, host, port
    s.listen(3)
    conn, addr = s.accept()
    print('Connected by', addr)
    conn.sendall(bytearray('Welcome'))

    p = PlotThread(_queue)
    p.start()
    s.setblocking(0)
    try:
        while True:
            data = conn.recv(1024)
            if not data: break
            for i,parts in enumerate(data.split('*')):
                if parts:
                    _queue.put(parts)

    except KeyboardInterrupt or ValueError as e:
        print e
    finally:
        p.exit()
    print "Closed connection"
    conn.close()
