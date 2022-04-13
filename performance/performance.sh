#!/bin/bash

NOW=$( date '+%F_%H:%M:%S' )

# echo
# echo ---- LATENCY TESTS ----
# echo

# echo First Run:
python3 receiver.py "$NOW" latency 100 &
python3 sender.py "$NOW" latency 100 --surb FALSE & 


python3 receiver.py "$NOW" surb_prep 10000 &
python3 receiver.py "$NOW" latency 100 &
python3 sender.py "$NOW" latency 100 --surb TRUE & 

# wait

# echo Second Run:
# python3 receiver.py "$NOW" latency 1000 &
# python3 sender.py "$NOW" latency 1000 &

# wait

# echo Third Run:
# python3 receiver.py "$NOW" latency 10000 &
# python3 sender.py "$NOW" latency 10000 &

# wait

# python3 calc_performance.py "$NOW" latency 100 1000 10000

# echo
# echo ---- THROUGHPUT TESTS ----
# echo

# Throughput: With SURB

# echo 1st Run With SURB:
# python3 receiver.py "$NOW" throughput 100 --surb TRUE &
# python3 sender.py "$NOW" throughput 100 --surb TRUE &

# wait

# echo 2nd Run With SURB:
# python3 receiver.py "$NOW" throughput 500 --surb TRUE &
# python3 sender.py "$NOW" throughput 500 --surb TRUE &

# wait

# echo 3rd Run With SURB:
# python3 receiver.py "$NOW" throughput 1000 --surb TRUE &
# python3 sender.py "$NOW" throughput 1000 --surb TRUE &

# wait 

# echo 4th Run With SURB:
# python3 receiver.py "$NOW" throughput 1500 --surb TRUE &
# python3 sender.py "$NOW" throughput 1500 --surb TRUE &

# wait 

# echo 5th Run With SURB:
# python3 receiver.py "$NOW" throughput 2000 --surb TRUE &
# python3 sender.py "$NOW" throughput 2000 --surb TRUE &

# wait 

# echo 6th Run With SURB:
# python3 receiver.py "$NOW" throughput 2500 --surb TRUE &
# python3 sender.py "$NOW" throughput 2500 --surb TRUE &

# wait 

# echo 7th Run With SURB:
# python3 receiver.py "$NOW" throughput 3000 --surb TRUE &
# python3 sender.py "$NOW" throughput 3000 --surb TRUE &

# wait 

# echo 8th Run With SURB:
# python3 receiver.py "$NOW" throughput 3500 --surb TRUE &
# python3 sender.py "$NOW" throughput 3500 --surb TRUE &

# wait 

# echo 9th Run With SURB:
# python3 receiver.py "$NOW" throughput 4000 --surb TRUE &
# python3 sender.py "$NOW" throughput 4000 --surb TRUE &

# wait 

# echo 10th Run With SURB:
# python3 receiver.py "$NOW" throughput 4500 --surb TRUE &
# python3 sender.py "$NOW" throughput 4500 --surb TRUE &

# wait 

# echo 11th Run With SURB:
# python3 receiver.py "$NOW" throughput 5000 --surb TRUE &
# python3 sender.py "$NOW" throughput 5000 --surb TRUE &

# wait 

# echo 12th Run With SURB:
# python3 receiver.py "$NOW" throughput 5500 --surb TRUE &
# python3 sender.py "$NOW" throughput 5500 --surb TRUE &

# wait 

# echo 13th Run With SURB:
# python3 receiver.py "$NOW" throughput 6000 --surb TRUE &
# python3 sender.py "$NOW" throughput 6000 --surb TRUE &

# wait 

# echo 14th Run With SURB:
# python3 receiver.py "$NOW" throughput 6500 --surb TRUE &
# python3 sender.py "$NOW" throughput 6500 --surb TRUE &

# wait 

# echo 15th Run With SURB:
# python3 receiver.py "$NOW" throughput 7000 --surb TRUE &
# python3 sender.py "$NOW" throughput 7000 --surb TRUE &

# wait 

# echo 16th Run With SURB:
# python3 receiver.py "$NOW" throughput 7500 --surb TRUE &
# python3 sender.py "$NOW" throughput 7500 --surb TRUE &

# wait 

# echo 17th Run With SURB:
# python3 receiver.py "$NOW" throughput 8000 --surb TRUE &
# python3 sender.py "$NOW" throughput 8000 --surb TRUE &

# wait 

# echo 18th Run With SURB:
# python3 receiver.py "$NOW" throughput 8500 --surb TRUE &
# python3 sender.py "$NOW" throughput 8500 --surb TRUE &

# wait 

# echo 19th Run With SURB:
# python3 receiver.py "$NOW" throughput 9000 --surb TRUE &
# python3 sender.py "$NOW" throughput 9000 --surb TRUE &

# wait

# echo 20th Run With SURB:
# python3 receiver.py "$NOW" throughput 9500 --surb TRUE &
# python3 sender.py "$NOW" throughput 9500 --surb TRUE &

# wait

# echo 21th Run With SURB:
# python3 receiver.py "$NOW" throughput 10000 --surb TRUE &
# python3 sender.py "$NOW" throughput 10000 --surb TRUE &

# wait

# Throughput: No SURB

# echo 1st Run Without SURB:
# python3 receiver.py "$NOW" throughput 100 --surb FALSE &
# python3 sender.py "$NOW" throughput 100 --surb FALSE &

# wait

# echo 2nd Run Without SURB:
# python3 receiver.py "$NOW" throughput 500 --surb FALSE &
# python3 sender.py "$NOW" throughput 500 --surb FALSE &

# wait

# echo 3rd Run Without SURB:
# python3 receiver.py "$NOW" throughput 1000 --surb FALSE &
# python3 sender.py "$NOW" throughput 1000 --surb FALSE &

# wait 

# echo 4th Run Without SURB:
# python3 receiver.py "$NOW" throughput 1500 --surb FALSE &
# python3 sender.py "$NOW" throughput 1500 --surb FALSE &

# wait 

# echo 5th Run Without SURB:
# python3 receiver.py "$NOW" throughput 2000 --surb FALSE &
# python3 sender.py "$NOW" throughput 2000 --surb FALSE &

# wait 

# echo 6th Run Without SURB:
# python3 receiver.py "$NOW" throughput 2500 --surb FALSE &
# python3 sender.py "$NOW" throughput 2500 --surb FALSE &

# wait 

# echo 7th Run Without SURB:
# python3 receiver.py "$NOW" throughput 3000 --surb FALSE &
# python3 sender.py "$NOW" throughput 3000 --surb FALSE &

# wait 

# echo 8th Run Without SURB:
# python3 receiver.py "$NOW" throughput 3500 --surb FALSE &
# python3 sender.py "$NOW" throughput 3500 --surb FALSE &

# wait 

# echo 9th Run Without SURB:
# python3 receiver.py "$NOW" throughput 4000 --surb FALSE &
# python3 sender.py "$NOW" throughput 4000 --surb FALSE &

# wait 

# echo 10th Run Without SURB:
# python3 receiver.py "$NOW" throughput 4500 --surb FALSE &
# python3 sender.py "$NOW" throughput 4500 --surb FALSE &

# wait 

# echo 11th Run Without SURB:
# python3 receiver.py "$NOW" throughput 5000 --surb FALSE &
# python3 sender.py "$NOW" throughput 5000 --surb FALSE &

# wait 

# echo 12th Run Without SURB:
# python3 receiver.py "$NOW" throughput 5500 --surb FALSE &
# python3 sender.py "$NOW" throughput 5500 --surb FALSE &

# wait 

# echo 13th Run Without SURB:
# python3 receiver.py "$NOW" throughput 6000 --surb FALSE &
# python3 sender.py "$NOW" throughput 6000 --surb FALSE &

# wait 

# echo 14th Run Without SURB:
# python3 receiver.py "$NOW" throughput 6500 --surb FALSE &
# python3 sender.py "$NOW" throughput 6500 --surb FALSE &

# wait 

# echo 15th Run Without SURB:
# python3 receiver.py "$NOW" throughput 7000 --surb FALSE &
# python3 sender.py "$NOW" throughput 7000 --surb FALSE &

# wait 

# echo 16th Run Without SURB:
# python3 receiver.py "$NOW" throughput 7500 --surb FALSE &
# python3 sender.py "$NOW" throughput 7500 --surb FALSE &

# wait 

# echo 17th Run Without SURB:
# python3 receiver.py "$NOW" throughput 8000 --surb FALSE &
# python3 sender.py "$NOW" throughput 8000 --surb FALSE &

# wait 

# echo 18th Run Without SURB:
# python3 receiver.py "$NOW" throughput 8500 --surb FALSE &
# python3 sender.py "$NOW" throughput 8500 --surb FALSE &

# wait 

# echo 19th Run Without SURB:
# python3 receiver.py "$NOW" throughput 9000 --surb FALSE &
# python3 sender.py "$NOW" throughput 9000 --surb FALSE &

# wait

# echo 20th Run Without SURB:
# python3 receiver.py "$NOW" throughput 9500 --surb FALSE &
# python3 sender.py "$NOW" throughput 9500 --surb FALSE &

# wait

# echo 21th Run Without SURB:
# python3 receiver.py "$NOW" throughput 10000 --surb FALSE &
# python3 sender.py "$NOW" throughput 10000 --surb FALSE &

# wait

