

#!/bin/bash
#!/usr/bin/env python3

export DISPLAY=:0 #needed if you are running a simple gui app.

cd "$(dirname "$0")"

process=script_ntp
while true
do


    if ! ps aux | grep -v grep | grep 'python3 NTP.py --location JATIASIH DEV' > /dev/null
    then #
        python3 NTP.py --location 'JATIASIH DEV'  &
        sleep 30 #
    fi #
sleep 10
done
exit
                