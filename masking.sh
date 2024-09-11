

#!/bin/bash
#!/usr/bin/env python3

export DISPLAY=:0 #needed if you are running a simple gui app.

cd "$(dirname "$0")"

process=script__masking_ntp

python3 masking.py  --rtsp rtsp://admin:tahun2023 --rtsp2 @10.6.116.87:554/Streaming/Channels/101/ --masking "((135, 201), (220, 210), (800, 800), (1280, 800), (1280, 0), (9, 0), (73, 175))" --input_titik KM_122_A 
python3 masking.py  --rtsp rtsp://admin:tahun2023 --rtsp2 @10.6.116.88:554/Streaming/Channels/101/ --masking "((674, 714), (1184, 186), (1274, 1), (0, 0), (0, 720))" --input_titik KM_127_A 
python3 masking.py  --rtsp rtsp://admin:tahun2023 --rtsp2 @10.6.116.85:554/Streaming/Channels/101/ --masking "((203, 698), (123, 312), (185, 306), (617, 720), (1280, 720), (1280, 0), (0, 0), (17, 699))" --input_titik KM_105_A 
python3 masking.py --rtsp rtsp://admin:tahun2023 --rtsp2 @10.6.116.86:554/Streaming/Channels/101/ --masking "((0, 0), (0, 720), (150, 720), (120, 180), (181, 180), (605, 720), (1280, 720), (1280, 0))" --input_titik KM_122_B 

sleep 10
exit
