from __future__ import absolute_import
import glob, os, copy, pickle
import numpy as np
import unidecode
import time
import argparse

def load_syms(fpath):
    """
    Return a dict
    """
    res = {}
    f = open(fpath, "r")
    lines = f.readlines()
    f.close()
    for line in lines:
        line = line.strip()
        sym, num = line.split(" ")
        num = int(num)
        res[num] = sym
    return res

def load_syms_from_LM(fpath):
    """
    Return a dict
    """
    res = {}
    f = open(fpath, "r")
    lines = f.readlines()
    f.close()
    for i, line in enumerate(lines):
        line = line.strip()
        res[i] = line
    return res


def start(args):
    if args.syms_from_LM:
        syms = load_syms_from_LM(args.path_syms)
    else:
        syms = load_syms(args.path_syms)
    print("A total of {} syms in {}".format(len(syms), args.path_syms))
    print("Loaded syms_from_LM {}".format(args.syms_from_LM))
    f = open(args.path_res, "r")
    lines = f.readlines()
    f.close()
    f_res = open(args.path_out, "w")
    for line in lines:
        line = line.strip()
        name_line, text_syms = line.split(" ")[0], line.split(" ")[1:]
        text_syms = [syms[int(x)] for x in text_syms]
        text_syms = [x if x != args.space else " " for x in text_syms]
        text = "".join(text_syms)
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
    parser.add_argument('--path_syms', metavar='path_syms', type=str,
                    help='Path to the table of syms.')
    parser.add_argument('--path_res', metavar='path_syms', type=str,
                    help='Path to the RES with syms to translte. First column is the name of the line.')
    parser.add_argument('--path_out', metavar='path_syms', type=str,
                    help='Path to the output.')
    parser.add_argument('--space', metavar='space', type=str,
                    help='Path to the output.', default="<space>")
    parser.add_argument('--syms_from_LM', type=str2bool, nargs='?',
                        const=True, default=True,)
    parser.add_argument('--delimiter', metavar='delimiter', type=str,
                    help='delimiter.', default=" ")
    args = parser.parse_args()
    start(args)