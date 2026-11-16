#!/usr/bin/python
# -*- coding:utf-8 -*-
from bottle import get,post,run,route,request,template,static_file
from http.server import BaseHTTPRequestHandler, HTTPServer
from PCA9685 import PCA9685
import threading
import subprocess
import os
import socket
import time

pwm = PCA9685(0x40)
pwm.setPWMFreq(50)

#Set the Horizontal vertical servo parameters
HPulse = 1500  #Sets the initial Pulse
HStep = 0      #Sets the initial step length
VPulse = 1000  #Sets the initial Pulse
VStep = 0      #Sets the initial step length

start = int(time.time())

pwm.setServoPulse(1,HPulse)
pwm.setServoPulse(0,VPulse)

@get("/")
def index():
    return template("index")
    
@route('/<filename>')
def server_static(filename):
    return static_file(filename, root='./')

@route('/fonts/<filename>')
def server_fonts(filename):
    return static_file(filename, root='./fonts/')
    
@post("/cmd")
def cmd():
    global HStep,VStep
    code = request.body.read().decode()
    print ("code ",code)
    # speed = request.POST.get('speed')
    # print(code)
    # if(speed != None):

        # print(speed)
    if code == "stop":
        HStep = 0
        VStep = 0
        print("stop")
    elif code == "up":
        VStep = -5
        print("up")
    elif code == "down":
        VStep = 5
        print("down")
    elif code == "left":
        HStep = 5
        print("left")
    elif code == "right":
        HStep = -5
        print("right")
    return "OK"


def mjpeg_server():
    class MJPEGHandler(BaseHTTPRequestHandler):
        # 新增：屏蔽BaseHTTPRequestHandler的日志打印（如GET请求日志）
        def log_message(self, format, *args):
            return
        
        def do_GET(self):
            if self.path != "/stream":
                self.send_error(404)
                return

            self.send_response(200)
            self.send_header(
                "Content-Type",
                "multipart/x-mixed-replace; boundary=frame"
            )
            self.end_headers()

            proc = subprocess.Popen(
                [
                    "rpicam-vid",
                    "--codec", "mjpeg",
                    "--width", "640",
                    "--height", "480",
                    "--framerate", "15",
                    "--inline",
                    "--timeout","0",
                    "-o", "-"
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,  
                stdin=subprocess.DEVNULL,  
                bufsize=0
            )

            try:
                buffer = b""
                while True:
                    buffer += proc.stdout.read(1024)

                    # JPEG start/stop flag
                    start = buffer.find(b'\xff\xd8')
                    end   = buffer.find(b'\xff\xd9')

                    if start != -1 and end != -1 and end > start:
                        jpeg = buffer[start:end+2]
                        buffer = buffer[end+2:]

                        self.wfile.write(b"--frame\r\n")
                        self.wfile.write(b"Content-Type: image/jpeg\r\n")
                        self.wfile.write(
                            b"Content-Length: %d\r\n\r\n" % len(jpeg)
                        )
                        self.wfile.write(jpeg)
                        self.wfile.write(b"\r\n")
            except BrokenPipeError:
                pass
            finally:
                proc.kill()

    server = HTTPServer(("", 8081), MJPEGHandler)
    server.serve_forever()

def timerfunc():
    global HPulse,VPulse,HStep,VStep,pwm,start
    
    if(HStep != 0):
        HPulse += HStep
        if(HPulse >= 2500): 
            HPulse = 2500
        if(HPulse <= 500):
            HPulse = 500
        #set channel 2, the Horizontal servo
        pwm.start_PCA9685()
        pwm.setServoPulse(1,HPulse)
        start = int(time.time())        


    if(VStep != 0):
        VPulse += VStep
        if(VPulse >= 2500): 
            VPulse = 2500
        if(VPulse <= 500):
            VPulse = 500
        #set channel 3, the vertical servo
        pwm.start_PCA9685()
        pwm.setServoPulse(0,VPulse)   
        start = int(time.time())
        
    end = int(time.time())
    if((end - start) > 3):
        pwm.exit_PCA9685()
        start = int(time.time())

    
    global t        #Notice: use global variable!
    t = threading.Timer(0.02, timerfunc)
    t.start()
    
try:
    t2 = threading.Thread(target = mjpeg_server)
    t2.setDaemon(True)
    t2.start()
        
    t = threading.Timer(0.02, timerfunc)
    t.setDaemon(True)
    t.start()


    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 80))
    localhost = s.getsockname()[0]

    run(host=localhost, port="8001")
except:
    pwm.exit_PCA9685()
    print ("\nProgram end")
    exit()