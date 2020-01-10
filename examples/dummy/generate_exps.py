#!/usr/bin/env python3

"""
This file will generate N experiments into a given repo, using random paths for
them, a few different kinds and generating random data that looks somewhat
sensible to be able to simulate analysing results of experiments from a repo.

It uses the run_an_exp.py file to run the experiments.
"""

import argparse
import random
import subprocess

# crash program if this script is imported - it is meant to be run as a script
assert __name__ == "__main__", "do not import generate_exps.py"

parser = argparse.ArgumentParser()
parser.add_argument("--repo", type=str, default="./output")
parser.add_argument("-n", type=int, default=10, help="number of exps to generate")
parser.add_argument("--dry", action="store_true", default=False, help="only print out commands, don't run them")

args = parser.parse_args()

def random_float(min, max):
    interval = max-min
    start = min
    return lambda: random.random() * interval + start

def random_int(min, max):
    return lambda: random.randint(min, max)

params_to_sample = {
    "--lr": random_float(0.001, 0.1),
    "--gamma": random_float(0.1, 0.5),
    "--epochs": random_int(50, 100),
    "--beta": random_float(0.1, 0.5),
    "--optimizer": lambda: random.choice(["adam", "sgd", "adagrad"]),
    "--momentum": lambda: random.choice(["no", "nesterov"]),
    "--dropout": lambda: random.choice([0.4, 0.45, 0.5, 0.55, 0.6]),
}

processes = []

for i in range(args.n):
    params = ["./run_an_exp.py", "--repo", args.repo]
    for k, f in params_to_sample.items():
        params.append(k)
        params.append(str(f()))

    if args.dry:
        print(" ".join(params))
    else:
        processes.append(subprocess.Popen(params))

if not args.dry:
    exit_codes = [p.wait() for p in processes]
    print("finished, exit codes", exit_codes)
