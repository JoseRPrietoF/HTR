from __future__ import absolute_import
import glob, os, copy, pickle
from xml.dom import minidom
import numpy as np, cv2
from page import TablePAGE
import unidecode
# from threading import Thread
# from random import random
# import threading
import time
import multiprocessing
import argparse, math
from make_lines import get_all_xml, create_dir, load_image, get_rectangle, make_trans, crop_cv2, check_size, make_page_img, get_orientation_bl, make_page_img_twolines

SEM_MATCHING_TOKENS = {
    # 'column': ["ⓟ", "Ⓟ"], # or page
        'ai': ["ⓘ", "Ⓘ"],
        'am': ["ⓜ", "Ⓜ"],
        'af': ["ⓕ", "Ⓕ"],
        'ac': ["ⓒ", "Ⓒ"],
    # 'introduction-cartulaire': ["ⓑ", "Ⓑ"],
    # 'notice': ["ⓝ", "Ⓝ"],
    # 'censier': ["ⓔ", "Ⓔ"],
}

tokens = ["ⓘ", "Ⓘ", "ⓜ", "Ⓜ", "ⓕ", "Ⓕ", "ⓒ", "Ⓒ"]

def create_text(line, args):
    res = ""
    # line = line#.lower()
    # line = unidecode.unidecode(line)
    for w in line:
        # w = re.sub(r"[^a-zA-Z0-9 ]+", '', w) #REMOVED special chars
        if w == " ":
            w = "<space>"
        
        res += "{} ".format(w)
    if res == " " or not res or res == "":
        # print("Empty")
        res = "\""
    res = res.replace("< s e p >", args.sep)
    if not args.act_tokens:
        for token in tokens:
            res = res.replace(token, "")
    return res

def make_page_txt(fname, txts, path_out, Hmin, Wmin, args, line_set):
    page = TablePAGE(im_path=fname)
    tls = page.get_textLinesActs(SEM_MATCHING_TOKENS)
    basename = ".".join(fname.split(".")[:-1])
    basename = basename.split("/")[-1]
    n_deleted = 0
    for coords, text, id_line, bl, id_reg in tls:
        fname_line = "{}.{}".format(basename, id_line)
        check = check_size(coords, Hmin, Wmin, fname_line)
        if not check:
            print("not used {fname_line}")
            n_deleted += 1
            continue
        text = create_text(text, args)
        if fname_line not in line_set:
            txts.append([fname_line, text])
            line_set.add(fname_line)
        else:
            print(f'{fname_line} repeated')
    return n_deleted

def make_page_txt_twolines(fname, txts, path_out, Hmin, Wmin, args, line_set):
    page = TablePAGE(im_path=fname)
    tls = page.get_textLinesActs(SEM_MATCHING_TOKENS)
    basename = ".".join(fname.split(".")[:-1])
    basename = basename.split("/")[-1]
    n_deleted = 0
    for num_tl, [coords, text, id_line, bl, id_reg] in enumerate(tls):
        text2 = None
        if num_tl > 0 and num_tl < len(tls):
            coords2, text2, id_line2, bl2, id_reg2 = tls[num_tl-1]
            if id_reg2 == id_reg:
                text = f"{text2} {args.sep} {text}"
                # print(text)
        fname_line = "{}.{}".format(basename, id_line)
        check = check_size(coords, Hmin, Wmin, fname_line)
        if not check:
            print(f"not used {fname_line}")
            n_deleted += 1
            continue
        text = create_text(text, args)
        if fname_line not in line_set:
            txts.append([fname_line, text])
            line_set.add(fname_line)
        else:
            print(f'{fname_line} repeated')
    return n_deleted

def start(args):
    # Settings
    ext = args.ext_images
    n_hilos = args.threads
    Hmin, Wmin = args.min_size
    # Input
    path = args.path_input
    # Output
    path_out = args.path_out
    result_path = os.path.join(path_out, args.fname_table)
    result_path_trans = os.path.join(path_out, args.fname_trans)
    result_path_map = os.path.join(path_out, args.fname_trans_map)
    dest_img = os.path.join(path_out, args.dir_output_lines)

    ##############
    """
    Crop the lines
    """
    create_dir(path_out)
    create_dir(dest_img)
    files = get_all_xml(path)
    all_text = ""
    txts = []
    # Image
    
    if args.do_img:
        pool = multiprocessing.Pool(processes=n_hilos)              # start 4 worker processes
        for fname in files:
            make_page_img_twolines(fname, path_out, dest_img, ext, Hmin, Wmin, args)
            # if args.two_lines:
            #     pool.apply_async(make_page_img_twolines, [fname, path_out, dest_img, ext, Hmin, Wmin, args])
            # else:
            #     pool.apply_async(make_page_img, [fname, path_out, dest_img, ext, Hmin, Wmin, args])
        pool.close()
        pool.join()
    """
    Print the file with trans
    """
    print("Lines done")
    # Text
    n_deleted = 0
    line_set = set()
    for fname in files:
        if args.two_lines:
            n_del = make_page_txt_twolines(fname, txts, path_out, Hmin, Wmin, args, line_set)
        else:
            n_del = make_page_txt(fname, txts, path_out, Hmin, Wmin, args, line_set)
        n_deleted += n_del

    print("A total of {} files - {} lines".format(len(files), len(txts)))
    print("Deleted a total of {} lines under H {} and W {}".format(n_deleted, Hmin, Wmin))
    f_Result = open(result_path, "w")
    f_Result_trans = open(result_path_trans, "w")
    for fname_line, text in txts:
        f_Result.write("{} {}\n".format(fname_line, text))
        f_Result_trans.write("{}.png {}\n".format(fname_line, make_trans(text)))
        all_text += "{} ".format(text)
    f_Result.close()
    f_Result_trans.close()

    """
    Print the symbols
    """
    chars = all_text.split()
    chars = list(set(chars))
    chars.insert(0, "<ctc>")
    # for k,v in SEM_MATCHING_TOKENS.items():
    #     for vi in v:
    #         chars.append(vi)

    f_Result = open(result_path_map, "w")
    for i, c in enumerate(chars):
        f_Result.write("{} {}\n".format(c,i))
    f_Result.close()

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
    parser.add_argument('--threads', metavar='threads', type=int,
                    help='Number of processes to launch', default=4)
    parser.add_argument('--do_img', type=str2bool, nargs='?',
                        const=True, default=True,)
    parser.add_argument('--ext_images', metavar='ext_images', type=str,
                    help='Extension of the images. jpg, png, etc', default="jpg")
    parser.add_argument('--path_input', metavar='path_input', type=str,
                    help='Input path where are the xmls and images')
    parser.add_argument('--path_out', metavar='path_out', type=str,
                    help='Output path to store the results. The dir will be created if doesnt exist')
    parser.add_argument('--fname_table', metavar='fname_table', type=str,
                    help='Name of the output file to store the trans. Will be saved in path_out', default="table.txt")
    parser.add_argument('--fname_trans', metavar='fname_trans', type=str,
                    help='Name of the output file to store the trans. Will be saved in path_out', default="table.txt")
    parser.add_argument('--fname_trans_map', metavar='fname_trans_map', type=str,
                    help='Name of the output file to store the map of chars. Will be saved in path_out', default="trans.txt")
    parser.add_argument('--dir_output_lines', metavar='dir_output_lines', type=str,
                    help='Name of the output dir to store the lines. The dir Will be created in path_out', default="lines")
    parser.add_argument('--min_size', metavar='min_size', type=int, nargs=2,
                    help='Min sizes of Height and Width in pixels[H W]', default=[15, 15])
    parser.add_argument('--rotate', type=str2bool, nargs='?', help='Rotate lines or not',
                        const=True, default=False,)
    parser.add_argument('--angle_rot', metavar='angle_rot', type=int, 
                    help='Angle to rotate in case of rotate', default=90)
    parser.add_argument('--ratio_rotate', metavar='angle_rot', type=float, 
                    help='Rotate in case of this ratio: -> H/W <= ratio', default=0.5)
    parser.add_argument('--passau', type=str2bool, nargs='?',
                        const=True, default=False,)
    parser.add_argument('--normalized_grayscale', type=str2bool, nargs='?',
                        const=True, default=False,)
    parser.add_argument('--grayscale', type=str2bool, nargs='?',
                        const=True, default=False,)
    parser.add_argument('--crop_all', type=str2bool, nargs='?',
                        const=True, default=False,)
    parser.add_argument('--crop_baseline', type=str2bool, nargs='?',
                        const=True, default=False,)
    parser.add_argument('--height_from_baseline', type=int, default=128)
    parser.add_argument('--two_lines', type=str2bool, nargs='?',
                        const=True, default=False,)
    parser.add_argument('--act_tokens', type=str2bool, nargs='?',
                        const=True, default=False,)
    parser.add_argument('--line_Sep', type=int, default=5)
    parser.add_argument('--sep', metavar='fname_trans', type=str,
                    help='symbol as separator', default="<sep>")
    args = parser.parse_args()
    print("do_img - ", args.do_img)
    start(args)
