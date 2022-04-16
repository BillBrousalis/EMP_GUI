import tkinter as tk
import time
import pygame
import math
import OpenGL
from OpenGL.GL import *
from OpenGL.GLU import *
from pygame.locals import *
import serial
import threading
from OpenGL.raw.GL import *
import os

import serial_comms
import json



class ObjectClass():

    def __init__(self, root, embed, width, height):
        self.root = root
        self.embed = embed
        self.width = width
        self.height = height
        
        os.environ['SDL_WINDOWID'] = str(self.embed.winfo_id())
        os.environ['SDL_VIDEODRIVER'] = 'windib'
        
        try:
            self.ser = serial_comms.ser
            if self.ser.connect_state == "Connected":
                self.ser.serialFlush()

            else:
                print("serial was not connected during init of obj")
        except:
            print("init error in obj")        



    def init(self):
        glShadeModel(GL_SMOOTH)
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glClearDepth(1.0)
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)
        glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)


    def main(self):


        #self.ser = serial.Serial('COM16', 115200)
        
        #quat_send_string = 'vmon 7 100\n'
        #self.ser.send_data(quat_send_string)
        #print("SENDING... : " + quat_send_string) 
        

        video_flags = OPENGL | DOUBLEBUF
        pygame.init()
        screen = pygame.display.set_mode((self.width, self.height), video_flags)
        #pygame.display.set_caption("Orientation visualization")
        self.resizewin(self.width, self.height)
        pygame.display.init()
        pygame.display.flip()
        
        
        self.init()
        self.frames = 0
        self.ticks = pygame.time.get_ticks()
        self.update3d()



    def update3d(self):
        while self.ser.connect_state == "Connected" and self.ser.quat == True:
            try:                
                [w, nx, ny, nz] = self.read_data()
                self.draw(w, nx, ny, nz)
                pygame.display.flip()
                self.root.update()
                self.frames += 1
            except Exception as e:
                print("error in update3d...", e)





    def resizewin(self, width, height):
        """
        For resizing window
        """
        if height == 0:
            height = 1
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, 1.0*width/height, 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()





    def read_data(self):
        line = self.ser.receive_data()
        #line = json.loads(line)
        try:             
            #items = line.split(',')
            # line is already a dictionary
            items = line['md7']           
            
            w = items[0]        
            nx = items[1]     
            ny = items[2]      
            nz = items[3]
            #print(w, nx, ny, nz)
            return [w, nx, ny, nz]    
        except:
            print('3d read_data error...')


    def draw(self, w, nx, ny, nz):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(0, 0.0, -7.0)


        [yaw, pitch , roll] = self.quat_to_ypr([w, nx, ny, nz])
        
        glRotate(2 * math.acos(w) * 180.00/math.pi, nx, nz, (-1)*ny)
       

        glBegin(GL_QUADS)
        glColor3f(0.0, 1.0, 0.0)
        glVertex3f(1.0, 0.2, -1.0)
        glVertex3f(-1.0, 0.2, -1.0)
        glVertex3f(-1.0, 0.2, 1.0)
        glVertex3f(1.0, 0.2, 1.0)

        glColor3f(1.0, 0.5, 0.0)
        glVertex3f(1.0, -0.2, 1.0)
        glVertex3f(-1.0, -0.2, 1.0)
        glVertex3f(-1.0, -0.2, -1.0)
        glVertex3f(1.0, -0.2, -1.0)

        glColor3f(1.0, 0.0, 0.0)
        glVertex3f(1.0, 0.2, 1.0)
        glVertex3f(-1.0, 0.2, 1.0)
        glVertex3f(-1.0, -0.2, 1.0)
        glVertex3f(1.0, -0.2, 1.0)

        glColor3f(1.0, 1.0, 0.0)
        glVertex3f(1.0, -0.2, -1.0)
        glVertex3f(-1.0, -0.2, -1.0)
        glVertex3f(-1.0, 0.2, -1.0)
        glVertex3f(1.0, 0.2, -1.0)

        glColor3f(0.0, 0.0, 1.0)
        glVertex3f(-1.0, 0.2, 1.0)
        glVertex3f(-1.0, 0.2, -1.0)
        glVertex3f(-1.0, -0.2, -1.0)
        glVertex3f(-1.0, -0.2, 1.0)

        glColor3f(1.0, 0.0, 1.0)
        glVertex3f(1.0, 0.2, -1.0)
        glVertex3f(1.0, 0.2, 1.0)
        glVertex3f(1.0, -0.2, 1.0)
        glVertex3f(1.0, -0.2, -1.0)
        glEnd()




    def quat_to_ypr(self, q):
        yaw   = math.atan2(2.0 * (q[1] * q[2] + q[0] * q[3]), q[0] * q[0] + q[1] * q[1] - q[2] * q[2] - q[3] * q[3])
        pitch = -math.sin(2.0 * (q[1] * q[3] - q[0] * q[2]))
        roll  = math.atan2(2.0 * (q[0] * q[1] + q[2] * q[3]), q[0] * q[0] - q[1] * q[1] - q[2] * q[2] + q[3] * q[3])
        pitch *= 180.0 / math.pi
        yaw   *= 180.0 / math.pi
        yaw -= -4.13

        #yaw   -= -0.13  # Declination at Chandrapur, Maharashtra is - 0 degress 13 min
        roll  *= 180.0 / math.pi

        self.tk_roll = roll
        self.tk_pitch = pitch
        self.tk_yaw = yaw

        return [yaw, pitch, roll]

   