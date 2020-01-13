"""
This package is for adding officially supported integrations with other libraries.

The goal of the integrations is to make it easy to get started with dbx combined
with other frameworks. Features that an integration might add are:

- automatic loggic
- automatic checkpoints
- pause/resume functionality integrated with that of the other framework
- imports to from another framework format to dbx format (e.g. tensorboard to dbx)
- exports from dbx format to another framework format (e.g. dbx to tensorboard)
- and more.

Currently we only have a callback class for torchbearer which adds automatic
logging of some events. More integrations will be added in the future, depending
on user demand.

Are you using dbx or dbxlogger with other library or framework? Please share
back your work so others can benefit from it too. Simply sharing your experience
is also great so we can investigate together on how to create the best
integration.
"""
