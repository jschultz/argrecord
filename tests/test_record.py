#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argrecord
import argrecord.argreplay
import shutil
import os
import sys

#@gooey.Gooey()
def copy(argstring):
    parser = argrecord.ArgumentRecorder(os.path.realpath(__file__))
    parser.add_argument('-m', '--make', action='store_true', private=True)
    parser.add_argument('-l', '--log',  type=str, dest='log_file')
    parser.add_argument('-a', '--append', action='store_true')
    parser.add_argument('-b', '--backup', type=str)
    parser.add_argument('input_file',   type=str, input=True)
    parser.add_argument('output_file',  type=str, output=True)
    args = parser.parse_args(argstring)

    if not args.make or parser.replay_required(args):
        parser.write_comments(args, args.log_file, append=args.append, backup=args.backup)
        shutil.copyfile(args.input_file, args.output_file)
        return True
    else:
        return False

def test_copy():
    # Create new test input file
    inf = open("in.txt", "w")
    inf.write("test\n")
    inf.close()
    if os.path.isfile('out.txt'):
        os.remove('out.txt')

    print("Test file copies first time")
    assert(copy(['--make', '--log', 'copy.log', 'in.txt', 'out.txt']))
    print("Test file does not copy second time")
    assert(not copy(['--make', '--log', 'copy.log', 'in.txt', 'out.txt']))

    print("Test replay works")
    os.remove('out.txt')
    os.environ['PATH'] = 'tests' + os.pathsep + os.environ['PATH']
    # Redirect stdin so pytest doesn't freak out
    sys.stdin = open(os.devnull, 'r')
    argrecord.argreplay.main(['copy.log'])
    assert(os.path.isfile('out.txt'))

if __name__ == '__main__':
    copy(sys.argv[1:])