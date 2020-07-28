argrecord
=========

An extension to argparse to automate the generation of logfiles and self-describing output files, and provide a Make-like functionality to re-run a script based on those automatically generated logfiles.

Introduction
============

This library can be used in the place of `argparse <https://docs.python.org/3/library/argparse.html/>`_. It provides additional functionality to create and read logfiles or datafile headers to document the command that created them and re-run the same command.

Additional decorators such as `Gooey <https://pypi.org/project/Gooey/>`_ can still be used.

It works with Python 3.

The source code can be found at `argrecord <https://github.com/jschultz/argrecord/>`_.

Usage
=====

Recording script arguments
--------------------------

Simply replace ``argparse`` with ``argrecord`` and the class ``ArgumentParser`` with ``ArgumentRecorder``.

The ``ArgumentRecorder`` class provides three new methods:

``build_comments`` returns a multi-line string that represents the current script invocation; that is, the name of the script and the list arguments to it. We call these comments because they are designed to be included as the header of an output file and treated as a comment by whichever program subsequently treats the output file.

``write_comments`` writes the comments to a file. The file can be specified either as a filename or a file object of an output file. Additional arguments specify whether additional comments (for example from an input file) or comments in the already existing file should be appended to the comments generated from the argument parser, and whether an already existing file should be backed by by appending a suffix to its name.

Appending multiple sets of commments in a single logfile or output file allows the entire chain of commands the produced that file to be recorded.

``replay_required`` returns ``True`` or ``False`` indicating whether the script needs to be re-run. This is calculated by determining whether any of the input files to the script are newer than any of the currently existing output files.

The method ``add_argument`` takes three additional arguments.  ``input`` and ``output`` indicate whether the argument represents the name of a file that is an input or output of the script. ``private`` indicates that the argument should not be included in the comments.

Replaying script arguments
--------------------------

Default behaviour
.................

Run the script ``argreplay`` to re-run the commands that produced a logfile (or initial section of an output file). The default behaviour is to read a series of *recipes* from a logfile, detecting the name of the script and the input and output file(s) of each. Once it has read all the recipes, it processes them in reverse order. When it finds a command that needs to be re-run (because one or more of its input files is younger than one or more of its output files) it re-runs that command, then proceeds to the previous recipe. When a command is re-run, it typically creates a new output file that is an input file for the previous recipe, so that will in turn need to be re-run. The process continues until all the recipes have been processed, or a command returns an error.

Pipes
.....
``argreplay`` has some special features that allow it to replay sequences of commands in which the output of one is piped to the input of the next. When recording script arguments, if it encounters an input argument (one that was flagged with ``input``) but no argument value, it assumes that the input came from standard input. Likewise for output arguments and standard output. When replaying a sequence in which a command writing to standard output is followed by one reading from standard input, a pipe is established between those two commands. Such a sequence may be arbitrarily long.

Variable substitution
.....................
A recipe may include variables in its command arguments. For example,

    --year ${year}

In this case, ``argreplay`` must be given an argument ``--substitute`` that contains the variables to be substituted and the values with which to substitute them, with a colon as separator. For example, ``argreplay --substitute year:2019 ....``

Other options
.............

``--dry-run`` simply prints the commands that would be run. Note that since the command is not actually run, output files are not touched and subsequent commands that would be run will not be listed.

``--force`` means that the commands are run regardless of the timestamps on input and output file(s).

``--depth`` indicates how many recipes to read from a logfile. The default is to read all the recipes.

``--remove`` means that the logfile should be removed after it has been read but before any commands are run. This can help prevent the logfile growing too long if the commands will cause it to be extended.

``--gui`` causes `Gooey <https://pypi.org/project/Gooey/>`_ to be invoked if it is available.