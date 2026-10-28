#!/bin/bash
# model selection: number of layers chosen by held-out IoU (frames never seen in training)
cd "$(dirname "$0")"
for K in 3 4 5 6 7 8 10 12; do OMP_NUM_THREADS=1 PUPPET_SWEEP=1 PUPPET_K=$K python3 fit.py > cache/sweep_K$K.log 2>&1 & done
wait
