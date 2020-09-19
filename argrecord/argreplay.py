#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 Jonathan Schultz
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse
from argrecord import ArgumentRecorder, ArgumentReplay, ArgumentHelper
import os
import sys
import re
from datetime import datetime
import subprocess

try:
    import gooey
except ImportError:
    pass

# Work out whether the user wants gooey before gooey has a chance to strip the argument
gui = '--gui' in sys.argv
if gui:
    if 'gooey' not in sys.modules:
        raise ImportError("You must install Gooey to use --gui\nTry 'pip install gooey'")

    sys.argv.remove('--gui')

def add_arguments(parser):
    parser.description = "Replay command trails left by argrecord."

    if 'gooey' in sys.modules and not gui: # Add --gui argument so it appears in command usage.
        parser.add_argument('--gui', action='store_true', help='Open a window where arguments can be edited.')

    replaygroup = parser.add_argument_group('Replay')
    if gui:
        replaygroup.add_argument('input_file', type=str, widget='FileChooser', help='File to replay.')
    else:
        replaygroup.add_argument('input_file', type=str, nargs='+', help='Files to replay.')

    replaygroup.add_argument('-f', '--force',   action='store_true', help='Replay even if input file is not older than its dependents.')
    replaygroup.add_argument(      '--dry-run', action='store_true', help='Print but do not execute command')
    replaygroup.add_argument(      '--substitute', nargs='+', type=str, help='List of variable:value pairs for substitution')
    replaygroup.add_argument(      '--logfile',               type=str, help="Logfile for argreplay", private=True)

    advancedgroup = parser.add_argument_group('Advanced')
    advancedgroup.add_argument('-v', '--verbosity', type=int, private=True)
    advancedgroup.add_argument('-d', '--depth',     type=int, help='Depth of command history to replay, default is all.')
    advancedgroup.add_argument('-r', '--remove',   action='store_true', help='Remove input file before replaying.')

if gui:
    @gooey.Gooey(optional_cols=1, tabbed_groups=True)
    def parse_arguments(argstring):
        parser = gooey.GooeyParser()
        add_arguments(parser)
        args = parser.parse_args(argstring)
        return args
else:
    def parse_arguments(argstring):
        parser = ArgumentRecorder()
        add_arguments(parser)
        args, extra_args = parser.parse_known_args(argstring)
        if '--ignore-gooey' in extra_args:   # Gooey adds '--ignore-gooey' when it calls the command
            extra_args.remove('--ignore-gooey')

        if args.logfile:
            logfile = open(args.logfile, 'w')
            parser.write_comments(args, logfile, incomments=ArgumentHelper.separator())
            logfile.close()

        args.extra_args = extra_args
        args.substitute = { sub.split(':')[0]: sub.split(':')[1] for sub in args.substitute } if args.substitute else {}
        return args

def main(argstring=None):
    args = parse_arguments(argstring)

    if not isinstance(args.input_file, list):    # Gooey can't handle args.input_file as list
        args.input_file = [args.input_file]

    for infilename in args.input_file:
        if (args.verbosity or 1) >= 1:
            print("Replaying " + infilename, file=sys.stderr)

        infile = open(infilename, 'r')

        curdepth = 0
        replaystack = []
        replay = ArgumentReplay(infile, args.substitute)
        while replay.command:
            pipestack = [replay.command + args.extra_args]
            outputs = replay.outputs
            inputs = replay.inputs
            while replay.command and replay.inpipe:
                replay = ArgumentReplay(infile, args.substitute)
                inputs = replay.inputs
                if replay.command:
                    if replay.outpipe:
                        pipestack.append(replay.command + args.extra_args)
                    else:
                        # This corner case is a bit messy
                        replaystack.append((pipestack, inputs, outputs))
                        pipestack = None
                        break

            if pipestack:
                replaystack.append((pipestack, inputs, outputs))
            else:
                pipestack = [replay.command + args.extra_args]
                outputs = replay.outputs
                inputs = replay.inputs

            curdepth += 1
            if args.depth and curdepth >= args.depth:
                break

            if replay.command:
                replay = ArgumentReplay(infile, args.substitute)

        if replaystack:
            (pipestack, inputs, outputs) = replaystack.pop()
        else:
            pipestack = None

        while pipestack:
            execute = args.force
            if not execute:
                latestinput    = ArgumentHelper.latest_timestamp(inputs)
                earliestoutput = ArgumentHelper.earliest_timestamp(outputs)
                execute = (not latestinput) or (not earliestoutput) or (latestinput > earliestoutput)

            if execute:
                if args.remove:
                    os.args.remove(infilename)

                process = None
                if (args.verbosity or 1) >= 2:
                    print ("Piping: ", str(len(pipestack)), " commands:", file=sys.stderr)
                while len(pipestack):
                    command = pipestack.pop()

                    if (args.verbosity or 1) >= 1:
                        print("Executing: " + ' '.join([item if ' ' not in item else '"' + item + '"' for item in command]), file=sys.stderr)

                    if not args.dry_run:
                        process = subprocess.Popen(command, text=True,
                                                   stdout=subprocess.PIPE if len(pipestack) else sys.stdout,
                                                   stdin=process.stdout if process else sys.stdin,
                                                   stderr=sys.stderr)
                if not args.dry_run:
                    process.wait()
                    if process.returncode:
                        raise RuntimeError("Error running script.")

            if replaystack:
                (pipestack, inputs, outputs) = replaystack.pop()
            else:
                pipestack = None

if __name__ == '__main__':
    main()
