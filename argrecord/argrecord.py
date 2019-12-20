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

class ArgumentRecorder(argparse.ArgumentParser):

    def __init__(self, *args, **kwargs):
        self.hiddenargs = []    # Has to be before super().__init__ ???
        self.positional = []
        self.dependencies = []
        super().__init__(*args, **kwargs)

    def add_argument(self, *args, **kwargs):
        hidden = kwargs.get('hidden', False)
        if 'hidden' in kwargs:
            del kwargs['hidden']
        dependency = kwargs.get('dependency', False)
        if 'dependency' in kwargs:
            del kwargs['dependency']
        action = super().add_argument(*args, **kwargs)
        if not action.option_strings:
            self.positional += [ action.dest ]
        if hidden:
            self.hiddenargs += [ action.dest ]
        if dependency:
            self.dependencies += [ action.dest ]

    def build_comments(self, args, outfile=None):
        comments = ((' ' + outfile + ' ') if outfile else '').center(80, '#') + '\n'
        comments += '# ' + self.prog + '\n'
        for argname, argval in vars(args).items():
            if argname not in self.hiddenargs:
                if argname not in self.positional:
                    argspec = '--' + argname + '='
                else:
                    argspec = ''
                if argname in self.dependencies:
                    prefix = '##   '
                else:
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

    def write_comments(self, args, outfile=None, infile=None):
        incomments = ''
        if infile:
            if os.path.isfile(infile):
                fileobject = open(infile, 'r')

                while True:
                    line = fileobject.readline()
                    if line[:1] == '#':
                        incomments += line
                    else:
                        break

                fileobject.close()

        if outfile:
            fileobject = open(infile, 'w')
        else:
            fileobject = sys.stderr

        fileobject.write(self.build_comments(args))
        fileobject.write(incomments)
