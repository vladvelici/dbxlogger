#!/usr/bin/env python3

"""
This file will generate N experiments into a given repo, using random paths for
them, a few different kinds and generating random data that looks somewhat
sensible to be able to simulate analysing results of experiments from a repo.
"""

import random
import argparse

import dbxlogger as dbx

parser = argparse.ArgumentParser()
dbx.add_arguments_to(parser)
parser.add_argument("--lr", type=float)
parser.add_argument("--gamma", type=float)
parser.add_argument("--epochs", type=int)
parser.add_argument("--beta", type=float)
parser.add_argument("--optimizer", type=str)
parser.add_argument("--momentum", type=str)
parser.add_argument("--dropout", type=float)
args = parser.parse_args()

exp = dbx.Exp.new_from_args(args, kind="fake_exp", env=False)

exp.write()
logger = exp.logger()

# simulate some lr schedule
lr = args.lr

best_epoch = None

# generate random train and eval logs
for epoch_num in range(args.epochs):

    train_loss = random.random()

    logger("train/epoch/%d" % epoch_num, {
        "train_loss": train_loss,
        "lr": lr,
        "epoch_num": epoch_num,
    })

    val_acc = random.random() / 2 + 0.5,

    is_best = False
    if best_epoch is None:
        best_epoch = epoch_num
        best_epoch_acc = val_acc
        is_best = True
    elif best_epoch_acc < val_acc:
        is_best = True
        best_epoch_acc = val_acc
        best_epoch = epoch_num

    logger("train/epoch/%d/eval", {
        "val_loss": train_loss - (random.random() / 5),
        "val_acc": val_acc,
        "is_best": is_best,
        "epoch_num": epoch_num,
    })

    lr = args.lr * args.gamma

logger("train/summary", {
    "epochs": args.epochs,
    "best_val_acc": best_epoch_acc,
    "best_epoch": best_epoch,
    "last_val_acc": val_acc,
})
