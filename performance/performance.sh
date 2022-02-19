#!/bin/bash

NOW=$( date '+%F_%H:%M:%S' )

echo
echo ---- LATENCY TESTS ----
echo

echo First Run:
python3 receiver.py "$NOW" latency 100 &
python3 sender.py "$NOW" latency 100 &

wait

echo Second Run:
python3 receiver.py "$NOW" latency 1000 &
python3 sender.py "$NOW" latency 1000 &

wait

echo Third Run:
python3 receiver.py "$NOW" latency 10000 &
python3 sender.py "$NOW" latency 10000 &

wait

python3 calc_performance.py "$NOW" latency 100 1000 10000

# echo
# echo ---- THROUGHPUT TESTS ----
# echo

# echo First Run With SURB:
# python3 receiver.py "$NOW" throughput 100 --surb TRUE &
# python3 sender.py "$NOW" throughput 100 --surb TRUE &

# wait

# echo Second Run With SURB:
# python3 receiver.py "$NOW" throughput 1000 --surb TRUE &
# python3 sender.py "$NOW" throughput 1000 --surb TRUE &

# wait

# echo Third Run With SURB:
# python3 receiver.py "$NOW" throughput 10000 --surb TRUE &
# python3 sender.py "$NOW" throughput 10000 --surb TRUE &

# wait 

# echo Fourth Run With SURB:
# python3 receiver.py "$NOW" throughput 100000 --surb TRUE &
# python3 sender.py "$NOW" throughput 100000 --surb TRUE &

# wait 

#python3 calc_performance.py "$NOW" throughput 100 1000 10000 100000

# wait

# echo First Run Without SURB:
# python3 receiver.py "$NOW" throughput 100 --surb FALSE &
# python3 sender.py "$NOW" throughput 100 --surb FALSE &

# wait

# echo Second Run Without SURB:
# python3 receiver.py "$NOW" throughput 1000 --surb FALSE &
# python3 sender.py "$NOW" throughput 1000 --surb FALSE &

# wait

# echo Third Run Without SURB:
# python3 receiver.py "$NOW" throughput 10000 --surb FALSE &
# python3 sender.py "$NOW" throughput 10000 --surb FALSE &

# wait 

# echo Fourth Run Without SURB:
# python3 receiver.py "$NOW" throughput 100000 --surb FALSE &
# python3 sender.py "$NOW" throughput 100000 --surb FALSE &

# wait 

# python3 calc_performance.py "$NOW" throughput 100 1000 10000 100000
