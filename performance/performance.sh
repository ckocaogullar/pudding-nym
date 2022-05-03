#!/bin/bash

NOW=$( date '+%F_%H:%M:%S' )

# echo
# echo ---- LATENCY TESTS ----
# echo

echo ---- LATENCY TESTS ----
python3 receiver.py test "$NOW" 5 --surb FALSE &
python3 sender.py "$NOW" 5 --surb FALSE & 

wait 

# python3 receiver.py surb_prep 100

# wait

python3 receiver.py test "$NOW" 5 --surb TRUE &
python3 sender.py "$NOW" 5 --surb TRUE & 

wait 