#!/bin/bash
#/usr/bin/env python3

export DISPLAY=:0 #needed if you are running a simple gui app.

cd "$(dirname "$0")"

process=script_ntp
while true
do

    # if ! ps aux | grep -v grep | grep 'python3 main1_new.py --rtsp rtsp://admin:tahun2023 --rtsp2 @10.6.116.87:554/Streaming/Channels/101/ --delay 20 --nocctv 1' > /dev/null
    # then #--nocctv 1
    #     python3 main1_new.py --rtsp rtsp://admin:tahun2023 --rtsp2 @10.6.116.87:554/Streaming/Channels/101/ --delay 20 --nocctv 1 --masking "((135, 201), (250, 210), (800, 800), (1280, 800), (1280, 0), (9, 0), (73, 175))" --input_titik KM_122_A --endpoint http://10.6.105.38:8200/status_auto &
    #     sleep 30 #--nocctv 1
    # fi #--nocctv 1

    if ! ps aux | grep -v grep | grep 'python3 main2_new.py --location CAWANG UKI' > /dev/null
    then #--nocctv 1
        python3 main2_new.py --location 'CAWANG UKI' &
        sleep 30 #--nocctv 1
    fi #--nocctv 1

sleep 10
done
exit
        