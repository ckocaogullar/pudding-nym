#!/bin/bash

NOW=$( date '+%F_%H:%M:%S' )

# echo
# echo ---- LATENCY TESTS ----
# echo

# echo ---- LATENCY TESTS ----
# python3 receiver.py latency "$NOW" 100 --surb FALSE&
# python3 sender.py latency "$NOW" 100 --surb FALSE & 

# wait 

python3 receiver.py surb_prep 10100

wait

# python3 receiver.py latency "$NOW" 100 --surb TRUE&
# python3 sender.py latency "$NOW" 100 --surb TRUE & 

# wait 

# echo ---- THROUGHPUT TESTS ----

# python3 receiver.py throughput "$NOW" 10 --surb FALSE &
# python3 sender.py throughput "$NOW" 10 --surb FALSE & 

# wait 

# python3 receiver.py throughput "$NOW" 100 --surb FALSE &
# python3 sender.py throughput "$NOW" 100 --surb FALSE & 

# wait 

# python3 receiver.py throughput "$NOW" 1000 --surb FALSE &
# python3 sender.py throughput "$NOW" 1000 --surb FALSE & 

# wait 

# python3 receiver.py throughput "$NOW" 10000 --surb FALSE &
# python3 sender.py throughput "$NOW" 10000 --surb FALSE & 

# wait 

# python3 receiver.py surb_prep 1200

# wait

# python3 receiver.py throughput "$NOW" 10 &
# python3 sender.py throughput "$NOW" 10 --surb TRUE & 

# wait

# python3 receiver.py throughput "$NOW" 100 &
# python3 sender.py throughput "$NOW" 100 --surb TRUE & 

# wait

# python3 receiver.py throughput "$NOW" 1000 &
# python3 sender.py throughput "$NOW" 1000 --surb TRUE & 

# wait

# python3 receiver.py surb_prep 10010

# wait 

# python3 receiver.py throughput "$NOW" 10000 &
# python3 sender.py throughput "$NOW" 10000 --surb TRUE & 

# wait

