# dbxlogger

This package helps create detailed structured logs for machine learning experiments. It is framework agnostic and written in pure python with few dependencies.

It does not support python 2.

> This is early stage code. Doesn't have any tests. It's meant to change a lot without warning. Expect a rollercoaster ride if you use it in your own research. It will lead to: loss of data, loss of experiments, loss or discoloration of hair, grey hair, wasted time - both yours and your GPU's. If you're still curious about this project I appreciate any feedback, bug reports, feature requests and pull requests.

## What's the goal of dbx?

1. To provide a simple yet fully-featured format of repository to store experiment results and logs.
2. To provide a clear spec of how to synchronize repositories.
3. To provide tools for saving experiments and logging into the specified format (dbxlogger addresses this directly).
4. To provide tools for the easy extraction and analysis of meaningful data from repositories.


## What's the difference between dbx and other machine learning experiment managers?

There are lots of experiment managers out there today. I personally found none to really fit my needs for experiment management. They either try to do too much are are too restrictive. I think the core of an experiment management tool should be about storing and querying experiments and results while having minimum impact on how experiment code is written and run. Nor it should have anything to do with how data is displayed, plotted, and so on, although visualisation and UIs provided as extensions or optional components could be very useful.

The core of dbx is the idea of experiment results repository. It's not about putting experiments in a central database or some local file format. It's about treating a set of experiments as part of a repository, similar to how git repositories work. Then this repository can be copied, synchronized with other repositories and queried for experiment data and results.

A repository can be stored on the local filesystem, remote filesystem or by using a server. Using a server gives you a few advantages, like the ability to create live queries (to generate live plots, create testing frameworks, remote start/stop experiments and so on).

Following this core idea, an experiment is simply a set of defined parameters and one or more log streams (we'll just call these logs). A log in dbx is a list of append-only immutable events. Each event has a name and some arbitrary data (anything JSON can store, can also be nested).

All experiment data is stored in the experiment logs and is accessed from there, by directly reading and processing the log with code or using queries.

This architecture enables a few important things:

- **Clear separation of components**. The only thing that links the server, logger, command line tools, and other possible parts are the repository format and API for querying one. A simple library tool can make querying a local repository and a remote repository the same for the programmer or researcher.
- **Use what you want**. Because components are separated, you can use what you want. Don't need a server? Don't use one.
- **Sync all directions**. Sync repositories server-to-server, local-to-local, server-to-local, etc. Copy at will, just like git repos.
- **Extensions**. It's easy to build extensions and use standard tools this way. No lock-in. Want to generate a special kind of plots? Fine, fire up a matplotlib script and query the data you need. Want to make a super cool testing framework for experiment logs? Fine, just fetch the logs and test away. Most importantly, because these extensions use the same repository format/API they can be reused in other projects and by other people.

## Status of the project + known limitations

There's still a few things to figure out. The development of this project will be in the open from now on (including all of the components) so you can follow the development here on GitHub.

Known limitations that needs to be addressed:

- [ ] meta.json currently assumes one experiment = one script run. this isn't necessarily true, we need a way to allow one experiment to have more runs. each run will have it's own code version, env vars, machine hostname, etc.

#### Tests

I'm not writing tests for this just yet. This is because I'm still changing what all of this is actually supposed to be doing. Writing tests just adds some extra time to iterating over ideas. When the repository format and other things become somewhat stable I'll be adding some tests.


## Other components of dbx

I'm keeping other components of dbx in different repos. They are even earlier stage then this one. A Go command line tool and server are coming soon, but first this logger needs a little more work. Just a little.


## Want to help? Great!

I'm trying to include as much info as possible on future plans and things I'm currently working on in this repo's [issues](/issues), [projects](/projects) and [wiki](/wiki).

If you have any suggestions, bug reports, feature requests please [open a new issue](/issues/new).
