import glob, os, cv2
import numpy as np

def read_text(fpath):
    f = open(fpath, "r")
    line = f.readlines()
    line = " ".join(line)
    f.close()
    #line = line.strip()
    res = ""
    for w in line:
        if w == " ":
            w = "<space>"
        res += "{} ".format(w.lower())
    return res

def resize(img, size=(1024,768)):
    return cv2.resize(img.astype('float32'), size)

do_resize = True
tr_txt_table = "/data/cristo/data_CRISTO_SALVADOR/TRANSCR/TXT-Lineas-filtradas"
img_dirs = "/data/cristo/data_CRISTO_SALVADOR/LINEAS_PGM"
result_path = "/data2/jose/projects/HTR/works/cristo/tr_heightResized.txt"
result_path_map = "/data2/jose/projects/HTR/works/cristo/syms"
dest_img = "/data/cristo/data_CRISTO_SALVADOR/LINEAS_PGM_heightResized"
#dest_img = "/data/cristo/data_CRISTO_SALVADOR/LINEAS_PGM_2"
list_files = glob.glob("{}/*pgm".format(img_dirs))
f_Result = open(result_path, "w")
all_text = ""
sizes_W, sizes_H = [], []
for fname in list_files:
    name_id = fname.split("/")[-1].split(".")[0]
    fpath_text = os.path.join(tr_txt_table, "{}.txt".format(name_id))
    try:
        txt = read_text(fpath_text)
        #print(name_id, txt)
    except:
        print("Fallo en {}".format(fpath_text))
    fname_resized = os.path.join(dest_img, name_id)
    fname_resized = fname_resized.strip()
    txt = txt.rstrip()
    f_Result.write("{} {}\n ".format(fname_resized, txt))
    all_text += "{} ".format(txt)
    if do_resize:
        img = cv2.imread(fname)
        sizes_W.append(img.shape[1])
        sizes_H.append(img.shape[0])
        #dest_img
f_Result.close()

if not os.path.exists(dest_img):
    os.mkdir(dest_img)

if do_resize:
    print("Mean W {} H {}".format(np.mean(sizes_W), np.mean(sizes_H)))
    print("MAX W {} H {}".format(np.max(sizes_W), np.max(sizes_H)))
    print("MIN W {} H {}".format(np.min(sizes_W), np.min(sizes_H)))
    W,H = int(np.mean(sizes_W)), int(np.mean(sizes_H))
    for fname in list_files:
        #name_id = fname.split("/")[-1]
        name_id = fname.split("/")[-1].split(".")[0]
        fpath_text = os.path.join(dest_img, name_id+".png")

        img = cv2.imread(fname)
        h_img, w_img = img.shape[0], img.shape[1]
        size = (H, w_img)
        print(size)
        img = resize(img, size=size)
        imparams = [cv2.IMWRITE_PNG_COMPRESSION, 0]
        cv2.imwrite(fpath_text, img, imparams)
        #dest_img
chars = all_text.lower().split()
chars = list(set(chars))
chars.insert(0, "<ctc>")

f_Result = open(result_path_map, "w")
for i, c in enumerate(chars):
    f_Result.write("{} {}\n".format(c,i))
f_Result.close()
