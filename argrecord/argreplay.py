#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2017 Jonathan Schultz
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
from argrecord import ArgumentReplay
import os
import sys
import re
from datetime import datetime
import subprocess

# Work out whether the user wants gooey before gooey has a chance to strip the argument
gui = '--gui' in sys.argv
if gui:
    sys.argv.remove('--gui')
    try:
        import gooey
    except ImportError:
        raise ImportError("You must install Gooey to use --gui\nTry 'pip install gooey'")

def add_arguments(parser):
    parser.description = "Replay command trails left by argrecord."

    if not gui: # Add --gui argument so it appears in command usage.
        parser.add_argument('--gui', action='store_true', help='Open a window where arguments can be edited.')

    replaygroup = parser.add_argument_group('Replay')
    if gui:
        replaygroup.add_argument('input_file', type=str, widget='FileChooser', help='File to replay.')
    else:
        replaygroup.add_argument('input_file', type=str, nargs='+', help='Files to replay.')

    replaygroup.add_argument('-f', '--force',   action='store_true', help='Replay even if input file is not older than its dependents.')
    replaygroup.add_argument(      '--dry-run', action='store_true', help='Print but do not execute command')
    replaygroup.add_argument(      '--edit',    action='store_true', help='Add --gui argument when replaying commands. If supported, this will open a window to allow editing of the command arguments.')
    replaygroup.add_argument(      '--substitute', nargs='*', type=str, help='List of variable:value pairs for substitution')

    advancedgroup = parser.add_argument_group('Advanced')
    advancedgroup.add_argument('-v', '--verbosity', type=int, default=1)
    advancedgroup.add_argument('-d', '--depth',     type=int, help='Depth of command history to replay, default is all.')
    advancedgroup.add_argument('-r', '--remove',   action='store_true', help='Remove file before replaying.')

if gui:
    @gooey.Gooey(optional_cols=1, tabbed_groups=True)
    def parse_arguments():
        parser = gooey.GooeyParser()
        add_arguments(parser)
        args = parser.parse_args()
        return vars(args)
else:
    def parse_arguments():
        parser = argparse.ArgumentParser()
        add_arguments(parser)
        args, extraargs = parser.parse_known_args()
        if '--ignore-gooey' in extraargs:   # Gooey adds '--ignore-gooey' when it calls the command
            extraargs.remove('--ignore-gooey')
        args.extraargs = extraargs
        args.substitute = { sub.split(':')[0]: sub.split(':')[1] for sub in args.substitute } if args.substitute else {}
        return vars(args)

def argreplay(input_file, force, dry_run, edit,
              verbosity, depth, remove,
              extraargs=[], substitute={}, **dummy):

    if not isinstance(input_file, list):    # Gooey can't handle input_file as list
        input_file = [input_file]

    for infilename in input_file:
        if verbosity >= 1:
            print("Replaying " + infilename, file=sys.stderr)

        # Read comments at start of infile.
        cmd = ArgumentReplay.read_comments(infilename)
        print(cmd)

        if remove:
            os.remove(infilename)

        curdepth = 0
        replaystack = []
        filematch = False
        while len(comments) and not filematch:
            commentline = comments.pop(0)
            filematch = headerregexp.match(commentline)
        while filematch and len(comments):
            filename  = filematch.group('file')
            pipestack = []
            dependencylist = []
            outfile = None
            pipematch = True
            while pipematch and len(comments):
                commentline = comments.pop(0)
                cmdmatch = cmdregexp.match(commentline)
                if cmdmatch:
                    cmd = cmdmatch.group('cmd')
                else:
                    break

                arglist = []
                lastargname = ''
                commentline = comments.pop(0) if len(comments) else None
                argmatch = argregexp.match(commentline) if commentline else None
                while argmatch:
                    argdependency = argmatch.group('dependency')
                    argname       = argmatch.group('name')
                    argvalue      = argmatch.group('value')
                    print(argdependency, argname, argvalue)

                    if argvalue:
                        argvalsubs = substregexp.findall(argvalue)
                        for argvalsub in argvalsubs:
                            subname = argvalsub[1]
                            subval = substitute.get(subname)
                            if subval is None:
                                raise RuntimeError("Mising substitution: " + subname)

                            argvalue = argvalue.replace(argvalsub[0], subval)

                    if argdependency:
                        dependencylist.append(argvalue)

                    if argname and argname != lastargname:
                        arglist.append('--' + argname)
                        lastargname = argname

                    if argvalue is not None:
                        arglist.append(argvalue)

                    commentline = comments.pop(0) if len(comments) else None
                    argmatch = argregexp.match(commentline) if commentline else None

                pipestack.append((cmd, arglist + extraargs))
                pipematch = piperegexp.match(commentline) if commentline else None

            replaystack.append((pipestack, dependencylist, filename))

            curdepth += 1
            if depth and curdepth == depth:
                break

            filematch = headerregexp.match(commentline) if commentline else None


        if replaystack:
            (pipestack, dependencylist, outfilename) = replaystack.pop()
        else:
            pipestack = None

        execute = force
        while pipestack:
            if not execute:
                if not outfilename or not os.path.isfile(outfilename):
                    execute = True
                else:
                    outfilestamp = datetime.utcfromtimestamp(os.path.getmtime(outfilename))
                    if not dependencylist:
                        execute = True
                    for dependency in dependencylist:
                        if not os.path.isfile(dependency):
                            raise RuntimeError("Missing dependency: " + dependency)
                        dependencystamp = datetime.utcfromtimestamp(os.path.getmtime(dependency))
                        if dependencystamp > outfilestamp:
                            execute = True
                            break

            if execute:
                process = None
                while len(pipestack):
                    (cmd, arglist) = pipestack.pop()
                    if len(pipestack) == 0 and '--outfile' not in arglist and outfilename:
                        arglist = arglist + ['--outfile', outfilename]

                    if edit:
                        arglist += ['--gui']

                    if verbosity >= 1:
                        print("Executing: " + cmd + ' ' + ' '.join(arglist), file=sys.stderr)

                    if not dry_run:
                        process = subprocess.Popen([cmd] + arglist,
                                                    stdout=subprocess.PIPE if len(pipestack) else sys.stdout,
                                                    stdin=process.stdout if process else sys.stdin,
                                                    stderr=sys.stderr)
                if not dry_run:
                    process.wait()
                    if process.returncode:
                        raise RuntimeError("Error running script.")
            else:
                if verbosity >= 2:
                    print("File not replayed: " + outfilename, file=sys.stderr)

            if replaystack:
                (pipestack, dependencylist, outfilename) = replaystack.pop()
            else:
                pipestack = None

def main():
    kwargs = parse_arguments()
    argreplay(**kwargs)

if __name__ == '__main__':
    main()
