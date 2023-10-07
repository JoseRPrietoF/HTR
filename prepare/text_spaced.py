from __future__ import absolute_import
import glob, os, copy, pickle
import numpy as np
import unidecode
import time
import argparse

def start(args):
    f = open(args.path_res, "r")
    lines = f.readlines()
    f.close()
    f_res = open(args.path_out, "w")
    for line in lines:
        line = line.strip()
        name_line, text_syms = line.split(" ")[0], line.split(" ")[1:]
        text_syms = " ".join(text_syms)
        text = ""
        for sym in text_syms:
            if sym == " ":
                text += args.space + " "
            else:
                text += sym + " "
        f_res.write("{} {}\n".format(name_line, text))
    f_res.close()

def str2bool(v):
    if isinstance(v, bool):
       return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process lines.')
    parser.add_argument('--path_res', metavar='path_syms', type=str,
                    help='Path to the RES with syms to translte. First column is the name of the line.')
    parser.add_argument('--path_out', metavar='path_syms', type=str,
                    help='Path to the output.')
    parser.add_argument('--space', metavar='space', type=str,
                    help='space.', default="<space>")
    parser.add_argument('--delimiter', metavar='delimiter', type=str,
                    help='delimiter.', default=" ")
    parser.add_argument('--syms_from_LM', type=str2bool, nargs='?',
                        const=True, default=True,)
    args = parser.parse_args()
    start(args)