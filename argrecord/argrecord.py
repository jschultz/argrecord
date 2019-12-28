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
from datetime import datetime
import re

class ArgumentRecorder(argparse.ArgumentParser):

    def add_argument(self, *args, **kwargs):
        private = kwargs.pop('private', False)
        output = kwargs.pop('output', False)
        input = kwargs.pop('input', False)
        action = super().add_argument(*args, **kwargs)
        action.private = private
        action.input = input
        action.output = output

    def build_comments(self, args, outfile=None):
        comments = ((' ' + outfile + ' ') if outfile else '').center(80, '#') + '\n'
        comments += '# ' + self.prog + '\n'
        for argname, argval in vars(args).items():
            action = next((action for action in self._actions if action.dest == argname), None)
            if action and not action.private:
                if action.option_strings:
                    argspec = action.option_strings[-1]
                else:
                    argspec = ''

                prefix = '#    '

                if type(argval) == str or (sys.version_info[0] < 3 and type(argval) == unicode):
                    comments += prefix + argspec + ' "' + argval + '"\n'
                elif type(argval) == bool:
                    if argval:
                        comments += prefix + argspec + '\n'
                elif type(argval) == list:
                    for valitem in argval:
                        if type(valitem) == str:
                            comments += prefix + argspec + ' "' + valitem + '"\n'
                        else:
                            comments += prefix + argspec + ' ' + str(valitem) + '\n'
                elif argval is not None:
                    comments += prefix + argspec + ' ' + str(argval) + '\n'

        return comments

    def write_comments(self, args, dest, prepend=True):
        incomments = ''
        if isinstance(dest, str):
            if os.path.isfile(dest) and prepend:
                fileobject = open(dest, 'r+')
            else:
                fileobject = open(dest, 'w')
        elif dest:
            fileobject = dest
        else:
            fileobject = sys.stderr
            prepend = False

        if prepend:
            while True:
                line = fileobject.readline()
                if line[:1] == '#':
                    incomments += line
                else:
                    break

            fileobject.seek(0)

        fileobject.write(self.build_comments(args))
        if prepend:
            fileobject.write(incomments)

        if dest:
            fileobject.close()

    def replay_required(self, args):
        earliestoutputtime = None
        argsdict = vars(args)
        for outputaction in self._actions:
            if outputaction.output:
                outfilename = argsdict.get(outputaction.dest, None)
                outputtime = datetime.utcfromtimestamp(os.path.getmtime(outfilename)) if os.path.isfile(outfilename) else None
                if (not earliestoutputtime) or outputtime < earliestoutputtime:
                    earliestoutputtime = outputtime

        latestinputtime = None
        for inputaction in self._actions:
            if inputaction.input:
                infilename = argsdict.get(inputaction.dest, None)
                inputtime = datetime.utcfromtimestamp(os.path.getmtime(infilename)) if os.path.isfile(infilename) else None
                if (not latestinputtime) or inputtime > latestinputtime:
                    latestinputtime = inputtime

        return latestinputtime is not None and ((not earliestoutputtime) or latestinputtime > earliestoutputtime)

class ArgumentReplay():

    headregexp = re.compile(r"^#+(?:\s+(?P<file>.+)\s+)?#+$", re.UNICODE)
    cmdregexp  = re.compile(r"^#\s+(?P<cmd>[\w\.-]+)", re.UNICODE)
    argregexp  = re.compile(r"^#\s+(?P<option_string>-[\w-]*)?(?:\s*(?P<quote>\"?)(?P<value>.+)(?P=quote))?", re.UNICODE)
    substexp   = re.compile(r"(\$\{?(\w+)\}?)", re.UNICODE)

    def read_comments(source):
        if isinstance(source, str):
            fileobject = open(source, 'r')
        elif source:
            fileobject = source
        else:
            fileobject = sys.stdin

        line = fileobject.readline()
        headmatch = ArgumentReplay.headregexp.match(line)
        if headmatch:
            line = fileobject.readline()
        cmdmatch = ArgumentReplay.cmdregexp.match(line)
        if cmdmatch:
            cmd = cmdmatch.group('cmd')
        else:
            raise RuntimeError("Unrecognised input line: " + line)

        result = [cmd]
        while True:
            line = fileobject.readline()

            argmatch = ArgumentReplay.argregexp.match(line) if line else None
            if not argmatch:
                break
            else:
                option_string  = argmatch.group('option_string')
                value = argmatch.group('value')

                if value:
                    subs = ArgumentReplay.substexp.findall(value)
                    for sub in subs:
                        subname = sub[1]
                        subval = substitute.get(subname)
                        if subval is None:
                            raise RuntimeError("Mising substitution: " + subname)

                        value = value.replace(sub[0], subval)

                if option_string:
                    print(option_string)
                    result.append(option_string)
                if value:
                    result.append(value)

        return result