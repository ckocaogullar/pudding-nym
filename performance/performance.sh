#!/bin/bash

NOW=$( date '+%F_%H:%M:%S' )

echo First Run:
python3 receiver.py "$NOW" 10&
python3 sender.py "$NOW" 10&

wait

echo Second Run:
python3 receiver.py "$NOW" 20&
python3 sender.py "$NOW" 20&

wait

echo Third Run:
python3 receiver.py "$NOW" 30&
python3 sender.py "$NOW" 30&

wait

python3 calc_performance.py "$NOW" 10 20 30
