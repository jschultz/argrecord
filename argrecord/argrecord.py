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

class ArgumentRecorder(argparse.ArgumentParser):

    def __init__(self, *args, **kwargs):
        self.privateargs = []
        self.positional = []
        self.inputs = []
        self.outputs = []
        self.commentfilename   = kwargs.pop('commentfilename',   None)
        self.commentfileobject = kwargs.pop('commentfileobject', None)
        super().__init__(*args, **kwargs)

    def add_argument(self, *args, **kwargs):
        private = kwargs.pop('private', False)
        output = kwargs.pop('output', False)
        input = kwargs.pop('input', False)
        action = super().add_argument(*args, **kwargs)
        if not action.option_strings:
            self.positional += [ action.dest ]
        if private:
            self.privateargs += [ action.dest ]
        if input:
            self.inputs += [ action.dest ]
        if output:
            self.outputs += [ action.dest ]

    def build_comments(self, args, outfile=None):
        comments = ((' ' + outfile + ' ') if outfile else '').center(80, '#') + '\n'
        comments += '# ' + self.prog + '\n'
        for argname, argval in vars(args).items():
            if argname not in self.privateargs:
                if argname not in self.positional:
                    argspec = '--' + argname + '='
                else:
                    argspec = ''

                prefix = '#    '

                if type(argval) == str or (sys.version_info[0] < 3 and type(argval) == unicode):
                    comments += prefix + argspec + '"' + argval + '"\n'
                elif type(argval) == bool:
                    if argval:
                        comments += prefix + argspec + '\n'
                elif type(argval) == list:
                    for valitem in argval:
                        if type(valitem) == str:
                            comments += prefix + argspec + '"' + valitem + '"\n'
                        else:
                            comments += prefix + argspec + str(valitem) + '\n'
                elif argval is not None:
                    comments += prefix + argspec + str(argval) + '\n'

        return comments

    def write_comments(self, args, filename=None, fileobject=None, readincomments=True):
        incomments = ''
        if not fileobject:
            if not filename:
                _fileobject = sys.stderr
                readincomments = False
            elif os.path.isfile(filename):
                _fileobject = open(filename, 'r+')
            else:
                _fileobject = open(filename, 'w')
                readincomments = False
        else:
            _fileobject = fileobject

        if readincomments:
            while True:
                line = _fileobject.readline()
                if line[:1] == '#':
                    incomments += line
                else:
                    break

            _fileobject.seek(0)

        if _fileobject:
            _fileobject.write(self.build_comments(args))
            _fileobject.write(incomments)

            if (not fileobject) and filename:
                _fileobject.close()

    def parse_known_args(self, *args, **kwargs):
        ret = super().parse_known_args(*args, **kwargs)
        if self.commentfilename or self.commentfileobject:
            self.write_comments(ret[0], filename=self.commentfilename, fileobject=self.commentfileobject)
        return ret

    def replay_required(self, args):
        earliestoutputtime = None
        argsdict = vars(args)
        for output in self.outputs:
            outfilename = argsdict.get(output, None)
            outputtime = datetime.utcfromtimestamp(os.path.getmtime(outfilename)) if os.path.isfile(outfilename) else None
            if (not earliestoutputtime) or outputtime < earliestoutputtime:
                earliestoutputtime = outputtime

        latestinputtime = None
        for input in self.inputs:
            infilename = argsdict.get(input, None)
            inputtime = datetime.utcfromtimestamp(os.path.getmtime(infilename)) if os.path.isfile(infilename) else None
            if (not latestinputtime) or inputtime > latestinputtime:
                latestinputtime = inputtime

        return latestinputtime is not None and ((not earliestoutputtime) or latestinputtime > earliestoutputtime)