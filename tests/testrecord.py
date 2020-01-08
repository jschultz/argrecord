#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argrecord
import shutil

#@gooey.Gooey()
def main():
    parser = argrecord.ArgumentRecorder()
    #parser = argparse.ArgumentParser("test")
    parser.add_argument('-m', '--make', action='store_true', private=True)
    parser.add_argument('-l', '--log',  type=str, dest='log_file')
    parser.add_argument('-p', '--prepend', action='store_true')
    parser.add_argument('-b', '--backup', type=str)
    parser.add_argument('input_file',   type=str, input=True)
    parser.add_argument('output_file',  type=str, output=True)
    args = parser.parse_args()


    if not args.make or parser.replay_required(args):
        print("Copying %s to %s" % (args.input_file, args.output_file))
        parser.write_comments(args, args.log_file, prepend=args.prepend, backup=args.backup)
        shutil.copyfile(args.input_file, args.output_file)

main()