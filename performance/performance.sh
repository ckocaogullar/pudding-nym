#!/bin/bash

NOW=$( date '+%F_%H:%M:%S' )

# echo
# echo ---- LATENCY TESTS ----
# echo


# python3 receiver.py test "$NOW" 100 --surb TRUE&
# python3 sender.py "$NOW" 100 --surb TRUE & 

# wait 

# echo ---- DUMP TESTS ----

# python3 receiver.py load "$NOW" 10000 --surb FALSE&
# python3 sender.py load "$NOW" 10000 --surb FALSE & 

# wait

# python3 receiver.py surb_prep 10000

# wait

# python3 receiver.py load "$NOW" 10000 --surb TRUE&
# python3 sender.py load "$NOW" 10000 --surb TRUE & 

# wait 

echo
echo ---- LATENCY TESTS ----
echo

# python3 receiver.py surb_prep 100

python3 receiver.py test "$NOW" 20000 --surb FALSE --freq 10 & 
python3 sender.py test "$NOW" 20000 --surb FALSE --freq 10 & 

wait 

