# MLVLogger

This package helps create detailed structured logs for machine learning experiments. It is framework agnostic and written in pure python with no dependencies.

It does not support python 2.

## What does MLVLogger do?

1. Creates a *standard* directory structure for your machine learning experiments.
2. Saves all the metadata for your experiment, including git branch and commit.
3. Gives a `Logger` object for saving all logs for your experiments.


## Core philosophy of the `MLV` project libraries

An experiment is made of three things:

1. The meta parameters (model hyper-parameters AND implementation-specific arguments),
2. The execution environment (code, environment variables, machine) for ALL scripts/programs that made up the experiment,
3. The log - the list of events that happened during the experiment.

The meta parameters and the execution environment are **immutable** with the exception that information can only be append to them if more (complementary) scripts for the same experiment are executed.

The log is the core of an experiment, the main source of information about what happened during the experiment. The log should include performance metrics (both accuracy and execution time), images, videos, plots, other information about the execution of the experiment.

The log is an **append-only list** of **immutable events** or log entries.

An **event** (or log entry) is the claim that *something* happened during the experiment. This *something* can be anything like

- a plot was generated,
- an epoch of training started or finished
- the training paused, started or resumed
- the evaluation of a metric has just been computed (e.g. just computed accuracy on validation at epoch 5),
- and more.

See an example directory structure generated with MLVLogger.

## Support for sub-experiments

This is best explained by an example from my work. I have a `./train.py` script that trains a network and produces, among other things, a checkpoint file `model_best.pth.tar` insisde the experiment folder. Let's say it's in `/storage/my_exp/model_best.pth.tar`. I also have a script called `./squeeze.py` (it's for pruning) that uses the checkpoints from `./train.py` scripts and creates other results... But I want to keep them grouped in a directory structure like the following:

    /storage/
        my_exp_1/
        |    meta.json
        |    log.jsonl
        |    model_best.tar.pth
        |    ...
        |    /squeeze/
        |    |    subexp_1/
        |    |    |    meta.json
        |    |    |    log.jsonl
        |    |    |    ...
        |    |    subexp_2/
        |    |    |    meta.jsonl
        |    |    |    log.jonl
        my_exp_2/
        |    meta.json
        |    log.jsonl
        |    model_best.tar.pth
        |    ...
        |    /squeeze/
        |    |    subexp_1/
        |    |    |    meta.json
        |    |    |    log.jsonl
        |    |    |    ...
        |    |    subexp_2/
        |    |    |    meta.jsonl
        |    |    |    log.jonl

This structure is easy to make simply by setting the `savedir` parameter in the sub-experiments to contain the path to the parent experiment followed by `"/squeeze"` (for example `savedir == "/storage/my_exp_1/squeeze/"` and `name == "subexp_1"`). But this is quite lengthy since we already pass the checkpoint path to the `./squeeze.py` script.

To achieve this fairly elegantly, we can add a function:

    import os
    # ...

    def init_squeeze_exp(checkpoint, name, params):
        c = os.path.basename(checkpoint)
        savedir = x[:len(checkpoint)-len(c)]
        savedir = os.path.join(savedir, "squeeze")
        return Exp(savedir, name, params, kind="squeeze")
