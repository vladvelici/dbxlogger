# dbxlogger

This package helps create detailed structured logs for machine learning experiments. It is framework agnostic and written in pure python with few dependencies.

It does not support python 2.

## State of this project

> This project is quite far from initial release that will be useful.

#### Logger

- [x] create log files using a logger directly.
- [x] `Logger` object can handle hierarchical events and has useful *navigation* methods.
- [x] non-blocking log writer using threading
- [x] non-blocking log writer using multiprocessing
- [x] handle `datetime.datetime` objects in log events
- [ ] tests for basic logging features

#### Experiment writer

- [x] write basic `meta.json` files
- [x] compute experiment ID (randomly generated)
- [x] methods to initialise loggers for different LogStreams inside the experiment
- [x] handle `--repo` and `--name`
- [x] save environment variables in meta
- [x] save git information in meta

## What does MLVLogger do?

1. Creates a *standard* directory structure for your machine learning experiments.
2. Saves all the metadata for your experiment, including git info and environment variables.
3. Gives a `Logger` object for saving all logs for your experiments.
4. Provides a few useful functions to display progress in the terminal window.
