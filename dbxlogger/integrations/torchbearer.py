import datetime

from dbxlogger.stopwatch import stopwatch

import torchbearer
from torchbearer.callbacks import Callback

class DbxCallback(Callback):

    def __init__(self, exp, logger=None):
        super(DbxCallback, self).__init__()
        self.exp = exp

        if type(logger) is str:
            self.logger = self.exp.logger(logger)
        elif logger:
            self.logger = logger
        else:
            self.logger = self.exp.logger()

        self._initial_logger_ctx = self.logger.ctx.path

    def reset_logger_ctx(self):
        self.logger.ctx.path = self._initial_logger_ctx

    def __str__(self):
        return "dbx.integrations.torchbearer.DbxCallback"

    def on_start(self, state):
        self.logger("start", {"timestamp": datetime.datetime.utcnow()})
        self._start_stopwatch = stopwatch()

    def on_start_epoch(self, state):
        self.reset_logger_ctx()
        self.logger.ctx.sub("epoch/%d" % state[torchbearer.state.EPOCH])

        self._epoch_event = self.logger.new_event("end", save_duration=True)

    def on_start_training(self, state):
        self._train_event = self.logger.new_event("training", save_duration=True)

    def on_end_training(self, state):
        self.logger.log(self._train_event)

    def on_start_validation(self, state):
        self._validation_event = self.logger.new_event("validation", save_duration=True)

    def on_end_validation(self, state):
        self.logger.log(self._validation_event)

    def on_end_epoch(self, state):
        metrics = state[torchbearer.state.METRICS]
        self._epoch_event.add(metrics)
        self.logger(self._epoch_event)
        self.reset_logger_ctx()

    def on_end(self, state):
        self.logger("done", {
            "timestamp": datetime.datetime.utcnow(),
            "duration": self._start_stopwatch(),
        })
