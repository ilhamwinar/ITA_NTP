#!/bin/bash
#!/usr/bin/env python3

#export DISPLAY=:1 #needed if you are running a simple gui app.

cd "$(dirname "$0")"

process=api_add_cctv2
while true
do

    if ! ps aux | grep -v grep | grep 'python3 api_add_cctv.py' > /dev/null
    then #{}
        python3 api_add_cctv.py &
        sleep 5 #{}
    fi #{}

done
exit
    