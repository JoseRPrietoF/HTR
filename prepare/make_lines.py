from __future__ import absolute_import
import glob, os, copy, pickle
from xml.dom import minidom
import numpy as np, cv2
from page import TablePAGE
import unidecode

from threading import Thread
from random import random
import threading
import time
import multiprocessing

progress = 0
result = None
result_available = threading.Event()

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
    minx, maxx = coords[0]
    miny, maxy = coords[0]
    for x, y in coords:
        if x < minx:
            minx = x
        if x > maxx:
            maxx = x
        if y < miny:
            miny = y
        if y > maxy:
            maxy = y
    return [minx, miny, maxx, maxy]

def create_text(line):
    res = ""
    for w in line:
        # w = re.sub(r"[^a-zA-Z0-9 ]+", '', w) #REMOVED special chars
        if w == " ":
            w = "<space>"
        w = unidecode.unidecode(w)
        res += "{} ".format(w.lower())
    return res

def crop_cv2(img, coords):
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

def make_page_img(fname, path_out):
    page = TablePAGE(im_path=fname)
    tls = page.get_textLines()
    basename = ".".join(fname.split(".")[:-1])
    img_path = "{}.{}".format(basename, ext)
    img = load_image(img_path)
    for coords, text, id_line in tls:
        # Get line-img
        # if "line_1525673888208_9287" not in id_line :
        #     continue
        line_img = crop_cv2(img, coords)
        fname_img_line = os.path.join(dest_img, "{}.png".format(id_line))
        cv2.imwrite(fname_img_line, line_img)
        text = create_text(text)
        fname_line = os.path.join(path_out, "{}".format(id_line))

def make_page_txt(fname, txts):
    page = TablePAGE(im_path=fname)
    tls = page.get_textLines()
    basename = ".".join(fname.split(".")[:-1])
    for coords, text, id_line in tls:
        text = create_text(text)
        fname_line = os.path.join(path_out, "{}".format(id_line))
        txts.append([fname_line, text])
    return txts

# Settings
ext = "jpg"
n_hilos = 4
# Input
path = "/data2/jose/corpus/tablas_DU/icdar_488/prueba/train"

# Output
# path_out = "/data2/jose/corpus/tablas_DU/icdar_488/prueba/train_out"
path_out = "prueba"
result_path = "{}/tr_prueba.txt".format(path_out)
result_path_map = "{}/syms".format(path_out)
dest_img = "{}/lines".format(path_out)

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
threads = []
pool = multiprocessing.Pool(processes=n_hilos)              # start 4 worker processes
for fname in files[:10]:
    # make_page_img(fname, path_out)

    # t = Thread(target=make_page_img, args=(fname, path_out, ))
    # threads.append(t)
    # t.start()
    result = pool.apply_async(make_page_img, [fname, path_out,])

# for index, thread in enumerate(threads):
#     thread.join()
pool.close()
pool.join()
"""
Print the file with trans
"""
# Text
for fname in files:
    make_page_txt(fname, txts)


f_Result = open(result_path, "w")
for fname_line ,text in txts[:10]:
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
