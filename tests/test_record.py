#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argrecord
import argrecord.argreplay
import shutil
import os
import sys

def copy(argstring):
    parser = argrecord.ArgumentRecorder(os.path.realpath(__file__))
    parser.add_argument('-m', '--make', action='store_true', private=True)
    parser.add_argument('-l', '--log',  type=str, dest='log_file')
    parser.add_argument('-a', '--append', action='store_true')
    parser.add_argument('-b', '--backup', type=str)
    parser.add_argument('--output_file',  type=str, output=True)
    parser.add_argument('input_file', nargs='?',  type=str, input=True)
    args = parser.parse_args(argstring)

    if not args.make or parser.replay_required(args):
        if args.log_file:
            parser.write_comments(args, args.log_file, append=args.append, backup=args.backup)
        infile = open(args.input_file, 'r') if args.input_file else sys.stdin
        outfile = open(args.output_file, 'w') if args.output_file else sys.stdout
        copy_buffer = infile.read(1024)
        while copy_buffer:
            outfile.write(copy_buffer)
            copy_buffer = infile.read(1024)
        if args.input_file:
            infile.close()
        if args.output_file:
            outfile.close()
        
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
    assert(copy(['--make', '--log', 'copy.log', '--output_file', 'out.txt', 'in.txt']))
    print("Test file does not copy second time")
    assert(not copy(['--make', '--log', 'copy.log', '--output_file', 'out.txt', 'in.txt']))

    print("Test replay works")
    os.environ['PATH'] = 'tests' + os.pathsep + os.environ['PATH']
    os.remove('out.txt')
    # Redirect stdin so pytest doesn't freak out
    sys.stdin = open(os.devnull, 'r')
    argrecord.argreplay.main(['copy.log'])
    assert(os.path.isfile('out.txt'))

    print("Test piping works")
    os.remove('out.txt')
    argrecord.argreplay.main(['test_pipe.log'])
    assert(os.path.isfile('out.txt'))

if __name__ == '__main__':
    copy(sys.argv[1:])