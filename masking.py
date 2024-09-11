import cv2
import os
from datetime import datetime
import time
import numpy as np
import argparse

## ARGUMENT PARSER PARAMETER
##--------------------------------------------------------------------------------------------------##
cur_dir = os.getcwd()
ap = argparse.ArgumentParser()

ap.add_argument("-r", "--rtsp", type=str,required=True,
	help="name of the user")
ap.add_argument("--rtsp2", type=str, required=True,
	help="name of the user")
ap.add_argument("-i", "--input_titik", type=str,required=True,
	help="input_titik")
ap.add_argument("-m", "--masking", type=str,required=True,
	help="masking")

args = vars(ap.parse_args())

# font 
font = cv2.FONT_HERSHEY_SIMPLEX 
# fontScale 
fontScale = 1
# Blue color in BGR 
color = (255, 255, 255) 
# Line thickness of 2 px 
thickness = 2


# ERROR HANDLING RTSP
RTSP_CAM1 = args["rtsp"]+args["rtsp2"]
if "null" in RTSP_CAM1:
    RTSP_CAM1= args["rtsp"]

masking1  = eval(args["masking"])
input_titik = args["input_titik"]

cap = cv2.VideoCapture(RTSP_CAM1)
while cap.isOpened():
    success, frame = cap.read()
    if success:
        waktu = datetime.now()

        MaskCoord=np.array((masking1))
        try:
            cv2.fillPoly(frame, pts=[MaskCoord], color=(0, 0, 0))
        except:
            pass
        
        now = datetime.now()
        date_time = now.strftime("%d-%m-%Y %H:%M:%S")
        cv2.putText(frame, input_titik, (150, 50) , font,  fontScale, color, thickness, cv2.LINE_AA) 
        cv2.putText(frame, date_time, (400, 50) , font,  fontScale, color, thickness, cv2.LINE_AA) 
        #save image
        cv2.imwrite(cur_dir+"/image/"+input_titik+".jpg", frame)

        break

cap.release()
cv2.destroyAllWindows()