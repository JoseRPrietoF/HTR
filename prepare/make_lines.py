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
import argparse
from scipy import ndimage

def get_all_xml(path, ext="xml"):
    file_names = glob.glob(os.path.join(path, "*{}".format(ext)))
    return file_names

def create_dir(p):
    if not os.path.exists(p):
        os.mkdir(p)

def load_image(path, size=None):
    image = cv2.imread(path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGBA)
    # image = cv2.normalize(image, None, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_32F)
    return image

def get_rectangle(coords):
    xs = np.array([x[0] for x in coords])
    ys = np.array([x[1] for x in coords])
    minx, miny, maxx, maxy = np.min(xs), np.min(ys), np.max(xs), np.max(ys)
    return [minx, miny, maxx, maxy]

def create_text(line):
    res = ""
    line = unidecode.unidecode(line)
    for w in line:
        # w = re.sub(r"[^a-zA-Z0-9 ]+", '', w) #REMOVED special chars
        if w == " ":
            w = "<space>"
        
        res += "{} ".format(w.lower())
    if res == " " or not res or res == "":
        # print("Empty")
        res = "\""
    return res

def crop_cv2(img, coords, Hmin, Wmin):
    rect = get_rectangle(coords)
    y=rect[1]
    x=rect[0]
    h=rect[3]-y
    w=rect[2]-x
    coords = np.array([[z[0]-x, z[1]-y] for z in coords])
    crop = img[y:y+h, x:x+w]
    crop[:,:,-1] = 0
    crop2 = crop.copy()
    cv2.fillConvexPoly(crop, coords, [0,0,0,255])
    crop2[:,:,-1] += crop[:,:,-1]
    return crop2

def check_size(coords, Hmin, Wmin):
    rect = get_rectangle(coords)
    y=rect[1]
    x=rect[0]
    h=rect[3]-y
    w=rect[2]-x
    if h<Hmin or w<Wmin:
        return False
    return True

def make_page_img(fname, path_out, dest_img, ext="jpg", Hmin=15, Wmin=15, args=None):
    page = TablePAGE(im_path=fname)
    tls = page.get_textLines()
    basename = ".".join(fname.split(".")[:-1])
    img_path = "{}.{}".format(basename, ext)
    img = load_image(img_path)
    basename = basename.split("/")[-1]
    for coords, text, id_line in tls:
        # Get line-img
        # if "line_1525862883289_1358" not in id_line :
        #     continue
        # else:
        #     print(coords)
        check = check_size(coords, Hmin, Wmin)
        if not check:
            continue
        line_img = crop_cv2(img, coords, Hmin, Wmin)
        fname_img_line = os.path.join(dest_img, "{}.{}.png".format(basename, id_line))
        height, width, channels = line_img.shape
        if args.rotate:
            ratio = width/height
            if ratio <= args.ratio_rotate:
                line_img = ndimage.rotate(line_img, args.angle_rot)
        cv2.imwrite(fname_img_line, line_img)

def make_page_txt(fname, txts, path_out, Hmin, Wmin):
    page = TablePAGE(im_path=fname)
    tls = page.get_textLines()
    basename = ".".join(fname.split(".")[:-1])
    basename = basename.split("/")[-1]
    n_deleted = 0
    for coords, text, id_line in tls:
        check = check_size(coords, Hmin, Wmin)
        if not check:
            n_deleted += 1
            continue
        text = create_text(text)
        # fname_line = os.path.join(path_out, "{}".format(id_line))
        fname_line = "{}.{}".format(basename, id_line)
        txts.append([fname_line, text])
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
    result_path = os.path.join(path_out, args.fname_trans)
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
            pool.apply_async(make_page_img, [fname, path_out, dest_img, ext, Hmin, Wmin, args])
        pool.close()
        pool.join()
    """
    Print the file with trans
    """
    print("Lines done")
    # Text
    n_deleted = 0
    for fname in files:
        n_del = make_page_txt(fname, txts, path_out, Hmin, Wmin)
        n_deleted += n_del

    print("A total of {} files - {} lines".format(len(files), len(txts)))
    print("Deleted a total of {} lines under H {} and W {}".format(n_deleted, Hmin, Wmin))
    f_Result = open(result_path, "w")
    for fname_line, text in txts:
        f_Result.write("{} {}\n".format(fname_line, text))
        all_text += "{} ".format(text)
    f_Result.close()

    """
    Print the symbols
    """
    chars = all_text.lower().split()
    chars = list(set(chars))
    chars.insert(0, "<ctc>")

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
    parser.add_argument('--fname_trans', metavar='fname_trans', type=str,
                    help='Name of the output file to store the trans. Will be saved in path_out', default="table.txt")
    parser.add_argument('--fname_trans_map', metavar='fname_trans_map', type=str,
                    help='Name of the output file to store the map of chars. Will be saved in path_out', default="syms")
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
    args = parser.parse_args()
    print("do_img - ", args.do_img)
    start(args)
