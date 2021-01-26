# NP2TechVodafone21
This Project was made for Vodafone Generation Next competition by Ilias Paschopoulos, Giannis Paschopoulos, Nikolas Ntermaris. The main idea for the project is a device that can check if someone is wearing a mask and at the same time measure his temperature. With this device a company for example can be sure if everyone maintain the protection measures.

## Requirements
This Project is running in a raspberry pi 4. It uses a WebCam in order to see if someone is wearing mask. After that it requires a thermal camera in order to calculate the temprature(we are using the Adafruit MLX90640). After that the Apache server should be installed in the raspberry pi in order to transfer the data through its Local IP.

## Software
After having the hardware ready we should also prepare the software. First the heart of the code is the file *main.py*. This file should be placed in the folder which the Apache *index.html* file is placed (ours is in /var/www/html). In this way the program can change the index file. Last replace the default *index.html* file from Apache and also add the *styleForRaspberry.css*.

## main.py
You can find more details in the code comments.