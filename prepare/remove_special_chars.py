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

def start(args):
    syms = load_syms(args.path_syms)
    syms = set([y for x,y in syms.items()])
    f = open(args.path_in, "r")
    lines = f.readlines()
    f.close()
    f_res = open(args.path_out, "w")
    print(syms)
    for line in lines:
        line = line.strip().lower()
        line = line.replace("§", "").replace("°", "").replace("%", "").replace("<stroke>", "").replace("[", "").replace("]", "").replace("·", "")
        name_line, text_syms = line.split(" ")[0], line.split(" ")[1:]
        text_syms_decoded = [unidecode.unidecode(x) for x in text_syms]
        text_syms_decoded = "".join(text_syms_decoded)
        text_syms_decoded = text_syms_decoded.replace("<space>", " ")
        res = ""
        for w in text_syms_decoded:
            if w == " ":
                w = "<space>"
            
            res += "{} ".format(w.lower())
        res = res.strip().split(" ")
        res2 = ""
        for x in res:
            if x not in syms and x != " ":
                print("not in syms:", x)
                print("problem with text_syms ", res)
                print("-> ", text_syms)
                print(line)
                print(unidecode.unidecode(line))
                exit()
            if x == " ":
                x = "<space>"
        
            res2 += "{} ".format(x.lower())     
        f_res.write("{} {}\n".format(name_line, res2))
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
    parser.add_argument('--path_in', metavar='path_syms', type=str,
                    help='Path to the RES with syms to translte. First column is the name of the line.')
    parser.add_argument('--path_out', metavar='path_syms', type=str,
                    help='Path to the output.')
    parser.add_argument('--path_syms', metavar='path_syms', type=str,
                    help='Path to the output.')                    
    args = parser.parse_args()
    start(args)