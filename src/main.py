import cv2
import time,board,busio
import numpy as np
from datetime import datetime
import random
import RPi.GPIO as GPIO
import adafruit_mlx90640  # Import the libraries

NickntConstant=1.135 # This is just a number to correct the temprature readings
THRESH = 60 # This value adjust the brightness (change if mask recognition dont work)
i2c = busio.I2C(board.SCL, board.SDA, frequency=400000) # Setup I2C
mlx = adafruit_mlx90640.MLX90640(i2c) # Begin MLX90640 with I2C comm
mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_16_HZ # Set refresh rate
mlx_shape = (24,32) 
GPIO.setmode(GPIO.BCM)
GPIO.setup(21, GPIO.OUT)
GPIO.setup(20, GPIO.OUT)
GPIO.setup(26, GPIO.OUT) # Set Led pins
frame = np.zeros((24*32,)) # Setup array for storing all 768 temperatures
t_array = []
def GetTemprature(): # This function returns the highest temprature readind of the thermal camera
    t1 = time.monotonic()
    mlx.getFrame(frame) # Read MLX temperatures into frame var
    data_array = (np.reshape(frame,mlx_shape)) # Reshape to 24x32
    t_array.append(time.monotonic()-t1)
    frame.sort()
    return frame[767] + NickntConstant # This is the final temp plus the constant

def RefreshHTML():
    Data = open("/var/www/html/data.txt", "r") # open the data file
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
    for i in range(len(Datalines)): # Change the HTML files dynamicaly depended on the data.txt file
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
    Html.writelines(Table)# Just write the new html code 
    Html.close()

def WriteData(x): # This function writes the data into the data.txt file
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
eyeCascade = cv2.CascadeClassifier('/var/www/html/haarcascade_eye.xml') # Load the haarcascades for the face recognition
cap = cv2.VideoCapture(0) # Start WebCam
cap.set(3, 640)  # set Width
cap.set(4, 480)  # set Height
RefreshHTML()
Testing = 0
while True: # Main loop
    FaceCounter = 0
    EyesCounter = 0
    MouthCounter = 0
    ret, img = cap.read()
    img = cv2.flip(img, 1)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    for i in range(5): # searching for face, eyes, mouth
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
    if EyesCounter == 0.0 and FaceCounter == 0.0 and len(facesTest) == 0:# Now the WebCam doesn't see anyone and it resets
        Testing = 0
        GPIO.output(20, GPIO.HIGH)
        GPIO.output(26, GPIO.LOW)
        GPIO.output(21, GPIO.LOW)
    elif Testing == 0:
        Testing = 1
    if Testing == 1:
       LastCheck = 0
       for x in range(5): # Just dont change it. It works... 
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

