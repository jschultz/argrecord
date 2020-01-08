argrecord

An extension to argparse to automate the generation of logfiles and self-describing files and provide a Make-like functionality to re-run a script.

============
Introduction
============

This library can be used in the place of `argparse <https://docs.python.org/3/library/argparse.html/>`_. It provides additional functionality to create and read logfiles or datafile headers to document the command that created them and re-run the same command.

Additional decorators such as `Gooey <https://pypi.org/project/Gooey/>`_ can still be used.

It works with Python 3.

The source code can be found at `argrecord <https://github.com/jschultz/argrecord/>`_.

=====
Usage
=====

Recording script arguments
--------------------------

Simply replace ``argparse`` with ``argrecord`` and the class ``ArgumentParser`` with ``ArgumentRecorder``.

The ``ArgumentRecorder`` class provides three new methods:

``build_comments`` returns a multi-line string that represents the arguments provided to the parser. We call these comments because they are designed to be included as the header of an output file and treated as a comment by whatever program subsequently treats the output file.

``write_comments`` writes the comments to a file. The file can be specified either as a filename or a file object of an output file. Additional arguments specify whether additional comments (for example from an input file) or comments in the already existing file should be appended to the comments generated from the argument parser, and whether an already existing file should be backed by by appending a suffix to its name.

Appending multiple sets of commments in a single logfile or output file allows the entire chain of commands the produced that file to be recorded.

``replay_required`` returns ``True`` or ``False`` indicating whether the script needs to be re-run. This is calculated by determining whether any of the input files to the script are newer than any of the currently existing output files.

The method ``add_argument`` takes three additional arguments.  ``input`` and ``output`` indicate whether the argument represents a filename that is an input or output of the script. ``private`` indicates that the argument should not be included in the list of comments.

Replaying script arguments
--------------------------

Run the script ``argreplay`` to re-run the commands that produced an output or logfile.

