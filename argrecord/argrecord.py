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
import sys
import os
import shutil
from datetime import datetime
import re
import io

class ArgumentHelper:

    @staticmethod
    def earliest_timestamp(filelist):
        result = None
        for filename in filelist:
            timestamp = datetime.utcfromtimestamp(os.path.getmtime(filename)) if os.path.isfile(filename) else None
            if (not result) or timestamp < result:
                result = timestamp

        return result

    @staticmethod
    def latest_timestamp(filelist):
        result = None
        for filename in filelist:
            timestamp = datetime.utcfromtimestamp(os.path.getmtime(filename)) if os.path.isfile(filename) else None
            if (not result) or timestamp > result:
                result = timestamp

        return result

    @staticmethod
    def read_comments(source):
        comments = ''
        if isinstance(source, str):
            fileobject = open(source, 'r')
        elif source is not None:    # Not sure why peekable object returns False
            fileobject = source
        else:
            fileobject = sys.stdin

        if hasattr(fileobject, 'seekable') and fileobject.seekable():
            while True:
                pos = fileobject.tell()
                line = fileobject.readline()
                if line[0] == '#':
                    comments += line
                else:
                    fileobject.seek(pos)
                    break
        else:
            if not hasattr(fileobject, 'peek'):
                raise RuntimeError("Source file object bust be seekable or peekable.")

            while True:
                peek = fileobject.peek()
                if peek[0] == '#':
                    comments += next(fileobject)
                else:
                    break

        if isinstance(source, str):
            fileobject.close()

        return comments

    @staticmethod
    def separator(header=None):
        return ((' ' + header + ' ') if header else '').center(80, '#') + '\n'

class ArgumentRecorder(argparse.ArgumentParser):

    def add_argument(self, *args, **kwargs):
        private = kwargs.pop('private', False)
        output = kwargs.pop('output', False)
        input = kwargs.pop('input', False)
        action = super().add_argument(*args, **kwargs)
        action.private = private
        action.input = input
        action.output = output
        
    def add_argument_group(self, *args, **kwargs):
        argument_group = super().add_argument_group(*args, **kwargs)
        argument_group.__class__ = _ArgumentGroup
        return(argument_group)

    def build_comments(self, args, outfile=None):
        comments = ArgumentHelper.separator(outfile)
        
        inpipe = False
        outpipe = False
        for argname, argval in vars(args).items():
            if argval is None:
                action = next((action for action in self._actions if action.dest == argname), None)
                if action:
                    if action.input:
                        inpipe = True
                    if action.output:
                        outpipe = True
                        
        comments += '#' + ('<' if inpipe else '') + ('>' if outpipe else '') + ' ' + self.prog + '\n'
        for argname, argval in vars(args).items():
            action = next((action for action in self._actions if action.dest == argname), None)
            if action and not action.private:
                if action.option_strings:
                    argspec = action.option_strings[-1]
                else:
                    argspec = ''

                prefix = '#' + ('<' if action.input else '>' if action.output else ' ') + '   '

                if type(argval) == str or (sys.version_info[0] < 3 and type(argval) == unicode):
                    comments += prefix + argspec + ' "' + argval + '"\n'
                elif type(argval) == bool:
                    if argval:
                        comments += prefix + argspec + '\n'
                elif type(argval) == list:
                    if argval:
                        for valitem in argval:
                            if type(valitem) == str:
                                comments += prefix + argspec + ' "' + valitem + '"\n'
                            else:
                                comments += prefix + argspec + ' ' + str(valitem) + '\n'
                            argspec = ' ' * len(argspec)
                    else:
                        comments += prefix + argspec + '\n'
                elif isinstance(argval, io.IOBase):
                    comments += prefix + argspec + ' "' + argval.name + '"\n'
                elif argval is not None:
                    comments += prefix + argspec + ' ' + str(argval) + '\n'

        return comments

    def write_comments(self, args, dest, outfile=None, incomments=None, append=False, backup=None):
        appendcomments = ''
        if isinstance(dest, str):
            if os.path.isfile(dest):
                if backup:
                    shutil.move(dest, dest + backup)
                    if append:
                        fileobject = open(dest + backup, 'r')
                elif append:
                    fileobject = open(dest, 'r')
            else:
                append = False
        elif dest:
            fileobject = dest
        else:
            fileobject = sys.stdout
            append = False

        if append:
            while True:
                line = next(fileobject, None)
                if line and line[:1] == '#':
                    appendcomments += line
                else:
                    break

            if isinstance(dest, str):
                fileobject.close()

        if isinstance(dest, str):
            fileobject = open(dest, 'w')

        fileobject.write(self.build_comments(args, outfile=outfile))
        if append:
            fileobject.write(appendcomments)
        if incomments:
            fileobject.write(incomments)

        if isinstance(dest, str):
            fileobject.close()

    def replay_required(self, args):
        argsdict = vars(args)
        earliestoutputtime = ArgumentHelper.earliest_timestamp([argsdict.get(action.dest) for action in self._actions if action.output])
        latestinputtime    = ArgumentHelper.latest_timestamp  ([argsdict.get(action.dest) for action in self._actions if action.input])

        return latestinputtime is not None and ((not earliestoutputtime) or latestinputtime > earliestoutputtime)

class _ArgumentGroup(argparse._ArgumentGroup):

    def add_argument(self, *args, **kwargs):
        private = kwargs.pop('private', False)
        output = kwargs.pop('output', False)
        input = kwargs.pop('input', False)
        action = super().add_argument(*args, **kwargs)
        action.private = private
        action.input = input
        action.output = output

class ArgumentReplay():

    headregexp = re.compile(r"^#+(?:\s+(?P<file>.+)\s+)?#+$", re.UNICODE)
    cmdregexp  = re.compile(r"^#(?P<inpipe>\<?)(?P<outpipe>\>?)\s+(?P<cmd>[\S]+)", re.UNICODE)
    argregexp  = re.compile(r"^#(?P<dependency>[<> ])\s*(?P<option_string>-[\w-]*)?\s*(?:(?P<quote>\"?)(?P<value>.+?)(?P<closequote>\"?))?$", re.UNICODE | re.DOTALL)

    substexp   = re.compile(r"(\$\{(\w+)\})", re.UNICODE)

    def __init__(self, source, substitute=None):
        self.command = []
        self.inpipe = False
        self.outpipe = False
        self.inputs = []
        self.outputs = []

        if isinstance(source, str):
            fileobject = open(source, 'r')
        elif source:
            fileobject = source
        else:
            fileobject = sys.stdin

        line = next(fileobject, None)
        if not line:
            return

        headmatch = ArgumentReplay.headregexp.match(line)
        if headmatch:
            line = next(fileobject, None)

        cmdmatch = ArgumentReplay.cmdregexp.match(line)
        if cmdmatch:
            self.command = [cmdmatch.group('cmd')]
            self.inpipe = cmdmatch.group('inpipe') == '<'
            self.outpipe = cmdmatch.group('outpipe') == '>'
        else:
            raise RuntimeError("Unrecognised input line: " + line)

        while True:
            line = next(fileobject, None)
            if not line:
                break

            argmatch = ArgumentReplay.argregexp.match(line.rstrip('\n'))
            if not argmatch:
                break
            else:
                if argmatch.group('quote') == '\"':
                    while argmatch.group('closequote') != argmatch.group('quote'):
                        line += next(fileobject, None)
                        argmatch = ArgumentReplay.argregexp.match(line)

                dependency = argmatch.group('dependency')
                option_string  = argmatch.group('option_string')
                value = argmatch.group('value')

                if value:
                    if dependency == '<':
                        self.inputs.append(value)
                    elif dependency == '>':
                        self.outputs.append(value)

                    subs = ArgumentReplay.substexp.findall(value)
                    for sub in subs:
                        subname = sub[1]
                        subval = substitute.get(subname)
                        if subval is None:
                            raise RuntimeError("Missing substitution: " + subname)

                        value = value.replace(sub[0], subval)

                if option_string:
                    self.command.append(option_string)
                if value:
                    self.command.append(value)

    def earliest_output():
        return ArgumentHelper.earliest_timestamp(self.outputs)

    def latest_input():
        return ArgumentHelper.latest_timestamp(self.inputs)
