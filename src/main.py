import cv2
import time,board,busio
import numpy as np
from datetime import datetime
import random
import RPi.GPIO as GPIO
import adafruit_mlx90640

NickntConstant=1.135 # value to change
THRESH = 60 # value to change
i2c = busio.I2C(board.SCL, board.SDA, frequency=400000) # setup I2C
mlx = adafruit_mlx90640.MLX90640(i2c) # begin MLX90640 with I2C comm
mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_16_HZ # set refresh rate
mlx_shape = (24,32)
GPIO.setmode(GPIO.BCM)
GPIO.setup(21, GPIO.OUT)
GPIO.setup(20, GPIO.OUT)
GPIO.setup(26, GPIO.OUT)
frame = np.zeros((24*32,)) # setup array for storing all 768 temperatures
t_array = []
def GetTemprature():
    t1 = time.monotonic()
    mlx.getFrame(frame) # read MLX temperatures into frame var
    data_array = (np.reshape(frame,mlx_shape)) # reshape to 24x32
    t_array.append(time.monotonic()-t1)
    frame.sort()
    return frame[767] + NickntConstant

def RefreshHTML():
    Data = open("/var/www/html/data.txt", "r")
    Datalines = Data.readlines()
    Data.close()
    Table = '<!DOCTYPE html>\n\
    <link rel="stylesheet" href="styleForRaspberry.css">\n\
    <html>\n\
    <body>\n\
    <table>\n\
    <tr>\n\
    <th>Temperature</th>\n\
    <th>Mask</th>\n\
    <th>Date</th>\n\
    </tr>\n'
    for i in range(len(Datalines)):
        Table = Table + "<tr>\n"
        Line = Datalines[i].split(",")
        if Line[0] <= "37":
            Table = Table + \
                '<td style="color:rgb(182, 255, 47);">' + Line[0] + '</td>\n'
        else:
            Table = Table + \
                '<td style="color:rgb(255, 78, 47);">' + Line[0] + '</td>\n'
        if Line[1] == "Yes":
            Table = Table + \
                '<td style="color:rgb(182, 255, 47);">' + Line[1] + '</td>\n'
        else:
            Table = Table + \
                '<td style="color:rgb(255, 78, 47);">' + Line[1] + '</td>\n'
        Table = Table + '<td>' + Line[2] + '</td>\n'
        Table = Table + '</tr>\n'
    Table = Table + '</table>\n\
    </body>\n\
    </html>'
    Html = open("/var/www/html/index.html", "w")
    Html.writelines(Table)
    Html.close()

def WriteData(x):
    temp = GetTemprature()
    now = datetime.now()
    Time = now.strftime("%d/%m/%Y %H:%M:%S")
    DataFile = open("/var/www/html/data.txt", "r")
    DataFilelines = DataFile.readlines()
    DataFile = open("/var/www/html/data.txt", "w")
    if len(DataFilelines) > 0:
        DataFilelines.append('\n'+str(temp)+","+x+","+Time)
    else:
        DataFilelines.append(str(temp)+","+x+","+Time)
    DataFile.writelines(DataFilelines)
    DataFile.close()

faceCascade = cv2.CascadeClassifier('/var/www/html/haarcascade_frontalface_default.xml')
mouthCascade = cv2.CascadeClassifier('/var/www/html/haarcascade_mcs_mouth.xml')
eyeCascade = cv2.CascadeClassifier('/var/www/html/haarcascade_eye.xml')
cap = cv2.VideoCapture(0)
cap.set(3, 640)  # set Width
cap.set(4, 480)  # set Height
RefreshHTML()
Testing = 0
while True:
    FaceCounter = 0
    EyesCounter = 0
    MouthCounter = 0
    ret, img = cap.read()
    img = cv2.flip(img, 1)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    for i in range(5):
       faces = faceCascade.detectMultiScale(
          gray,
          scaleFactor=1.2,
          minNeighbors=5,
          minSize=(20, 20)
       )
       mouths = mouthCascade.detectMultiScale(
          gray,
          scaleFactor=1.2,
          minNeighbors=5,
          minSize=(20, 20)
       )
       eyes = eyeCascade.detectMultiScale(
          gray,
          scaleFactor=1.2,
          minNeighbors=5,
          minSize=(20, 20)
       )
       MouthCounter += len(mouths)
       FaceCounter += len(faces)
       EyesCounter += len(eyes)
    (thresh, black_and_white) = cv2.threshold(gray, THRESH ,255, cv2.THRESH_BINARY)
    facesTest = faceCascade.detectMultiScale(
    black_and_white,
    scaleFactor=1.2,
    minNeighbors=5,
    minSize=(20, 20)
    )
    MouthCounter = MouthCounter/5
    FaceCounter = FaceCounter/5
    EyesCounter = EyesCounter/5
    if EyesCounter == 0.0 and FaceCounter == 0.0 and len(facesTest) == 0:
        Testing = 0
        GPIO.output(20, GPIO.HIGH)
        GPIO.output(26, GPIO.LOW)
        GPIO.output(21, GPIO.LOW)
    elif Testing == 0:
        Testing = 1
    if Testing == 1:
       LastCheck = 0
       for x in range(5):
          ret, img = cap.read()
          img = cv2.flip(img, 1)
          gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
          (thresh, black_and_white) = cv2.threshold(gray, THRESH ,255, cv2.THRESH_BINARY)
          facesTest = faceCascade.detectMultiScale(
          black_and_white,
          scaleFactor=1.2,
          minNeighbors=5,
          minSize=(20, 20)
          )
          LastCheck += len(facesTest)
       if LastCheck >=3:
          Testing = 2
          WriteData('No')
          RefreshHTML()
          print("NO MASK")
          GPIO.output(26, GPIO.HIGH)
          GPIO.output(20, GPIO.LOW)
       else:
          Testing = 2
          WriteData('Yes')
          RefreshHTML()
          print("YES MASK")
          GPIO.output(20, GPIO.LOW)
          GPIO.output(21, GPIO.HIGH)
    print("Face: " + str(FaceCounter) + "   Eyes: "+str(EyesCounter)+"     Mouth: "+str(MouthCounter)+"   Test: "+str(len(facesTest))+"     "+str(Testing))

