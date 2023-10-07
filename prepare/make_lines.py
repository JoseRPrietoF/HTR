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
from scipy import ndimage
import shapely
from shapely import affinity

def get_all_xml(path, ext="xml"):
    file_names = glob.glob(os.path.join(path, "*{}".format(ext)))
    print(os.path.join(path, "*{}".format(ext)))
    # file_names = [x for x in file_names if "CCA_CED_0117_0286" in x]
    # file_names = [x for x in file_names if "0245_0074" in x]
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

def create_text(line, args):
    res = ""
    # line = line#.lower()
    if args.passau:
        line = line.replace(" ", "")
        line = line.replace("&lt;space&gt;", " ")
        line = line.replace("&lt;ign&gt;", "")
        line = line.replace("<ign>", "")
        line = line.replace("<space>", " ")
    line = unidecode.unidecode(line)
    for w in line:
        # w = re.sub(r"[^a-zA-Z0-9 ]+", '', w) #REMOVED special chars
        if w == " ":
            w = "<space>"
        
        res += "{} ".format(w)
    if res == " " or not res or res == "":
        # print("Empty")
        res = "\""
    return res

def make_trans(t, args=None):
    t = t.replace(" ", "")
    t = t.replace("<space>", " ")
    return t

def crop_cv2(img, coords_tot, Hmin, Wmin, args, bl, top_tl=0, bot_tl=0):
    rect = get_rectangle(coords_tot)
    y=rect[1]
    x=rect[0]
    h=rect[3]-y
    w=rect[2]-x
    print(x, x+w)
    if not args.relative_to_bl:
        coords = np.array([[z[0]-x, z[1]-y] for z in coords_tot])
        crop = img[y:y+h, x:x+w]
        crop[:,:,-1] = 0
        crop2 = crop.copy()
    if args.crop_all:
        return crop2
    elif args.crop_baseline:
        if not bl:
            crop2 = crop2[:,:,:3]
        else:
            minx, miny, maxx, maxy = get_rectangle(bl)
            if args.relative_to_bl:
                add_top = int(top_tl) + args.top_relative_px
                add_bottom = int(bot_tl) + args.bot_relative_px
                add_top_alpha = 0
                add_bot_alpha = 0
                add_top = max(args.min_rel_height_top, min(add_top, args.max_rel_height_top))
                add_bottom = max(args.min_rel_height_bot, min(add_bottom, args.max_rel_height_bot))

                coords = np.array([[z[0]-minx, z[1]-y+add_top] for z in coords_tot])
                
                yavg = np.mean([x[1] for x in coords])
                l = []
                add = 0
                for x1,y1 in coords:
                    if y1 > yavg:
                        l.append([x1,y1+add_bot_alpha])
                    else:
                        l.append([x1,y1-add_top_alpha])
                coords = np.array(l, dtype=int)
                top = max(1, y-add_top)
                crop2 = img[top:y+h+add_bottom, minx:maxx].copy()
                crop = img[top:y+h+add_bottom, minx:maxx].copy()
                cv2.fillConvexPoly(crop, coords, [1,1,1,0])
                crop2 -= crop
                print(y,add_top, y-add_top)
                print(y, h, add_bottom, y+h+add_bottom)
                print(crop2.shape)
            else:
                min_coord = max(0, miny-args.height_from_baseline)
                crop2 = img[min_coord:miny+args.height_from_baseline, minx:maxx, :3]
    else:
        cv2.fillConvexPoly(crop, coords, [0,0,0,255])
        crop2[:,:,-1] += crop[:,:,-1]
    return crop2

def check_size(coords, Hmin, Wmin, fname_line=""):
    rect = get_rectangle(coords)
    y=rect[1]
    x=rect[0]
    h=rect[3]-y
    w=rect[2]-x
    
    if h<Hmin or w<Wmin or h == 0 or w == 0:
        # if "52681_001.line_1525315515070_1538" in fname_line:
        #     print(fname_line, y,x, "h", h, "w", w, "h<Hmin",  h<Hmin, "w<Wmin", w<Wmin, Hmin, Wmin)
        #     print(coords)
        #     exit()
        return False
    return True

def IoU_bl(bl1, bl2):
    # if bl2[0] >= bl1[0] and bl2[0] <= bl1[1]: #Izq dentro del rango
    #     return True
    # elif bl2[1] >= bl1[0] and bl2[0] <= bl1[1]: #Der dentro del rango
    #     return True
    # elif bl2[0] <= bl1[0] and bl2[1] >= bl1[1]:  # Todo dentro, ambos puntos fuera
    #     return True
    return (bl2[0] >= bl1[0] and bl2[0] <= bl1[1]) or (bl2[1] >= bl1[0] and bl2[0] <= bl1[1]) or (bl2[0] <= bl1[0] and bl2[1] >= bl1[1])
    # return False 

def get_relative_lines(bl, id_line, tls, args):
    minx, maxx = min([x[0] for x in bl]), max([x[0] for x in bl])
    avgy = np.mean([x[1] for x in bl])
    top_tl, bot_tl = 0, 0
    top_tl_distance, bot_tl_distance = 10000, 10000
    for coords2, text2, id_line2, bl2 in tls:
        if id_line == id_line2:
            continue
        # top 
        minx2, maxx2 = min([x[0] for x in bl2]), max([x[0] for x in bl2])
        if IoU_bl((minx, maxx), (minx2, maxx2)):
            avgy2 = np.mean([x[1] for x in bl2])
            d = avgy - avgy2
            if d > 0: #top tl
                if top_tl_distance >= d:
                    top_tl_distance = d
                    top_tl = d
            else: #bot tl
                d = abs(d)
                if bot_tl_distance >= d:
                    bot_tl_distance = d
                    bot_tl = d
    return top_tl, bot_tl

def make_page_img(fname, path_out, dest_img, ext="jpg", Hmin=15, Wmin=15, args=None):
    page = TablePAGE(im_path=fname)
    tls = page.get_textLines()
    basename = ".".join(fname.split(".")[:-1])
    img_path = "{}.{}".format(basename, ext)
    img = load_image(img_path)
    basename = basename.split("/")[-1]
    top_tl, bot_tl = 0, 0
    for coords, text, id_line, bl in tls:
        # Get line-img

        check = check_size(coords, Hmin, Wmin)
        if not check:
            print(f"not used {id_line}")
            continue
        if args.relative_to_bl:
            top_tl, bot_tl = get_relative_lines(bl, id_line, tls, args)
        line_img = crop_cv2(img, coords, Hmin, Wmin, args, bl, top_tl, bot_tl)
        if args.normalized_grayscale:
            # Normalized
            
            line_img = cv2.cvtColor(line_img, cv2.COLOR_BGR2GRAY)
            # line_img = ( line_img - line_img.min())/( line_img.max() - line_img.min())
            line_img = (line_img - np.mean(line_img)) / np.std(line_img)
            # line_img = cv2.normalize(line_img, None, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_32F)
            height, width = line_img.shape
        elif args.grayscale:
            # Normalized
            
            line_img = cv2.cvtColor(line_img, cv2.COLOR_BGR2GRAY)          
            height, width = line_img.shape
        else:
            height, width, channels = line_img.shape
        fname_img_line = os.path.join(dest_img, "{}.{}.png".format(basename, id_line))
        
        if height == 0 or width == 0:
            print("error ", fname_img_line)
        if args.rotate:
            # print(coords)
            orientation = get_orientation_bl(coords)
            # print(orientation)
            if orientation == "v":
                print(id_line, orientation, args.angle_rot)
                line_img = ndimage.rotate(line_img, args.angle_rot)
        print(fname_img_line)
        cv2.imwrite(fname_img_line, line_img)


def make_page_img_twolines(fname, path_out, dest_img, ext="jpg", Hmin=15, Wmin=15, args=None):
    page = TablePAGE(im_path=fname)
    tls = page.get_textLines_twolines()
    basename = ".".join(fname.split(".")[:-1])
    img_path = "{}.{}".format(basename, ext)
    img = load_image(img_path)
    basename = basename.split("/")[-1]
    for num_tl, [coords, text, id_line, bl, id_reg] in enumerate(tls):
        # Get line-img
        line_img2 = None
        if num_tl > 0 and num_tl < len(tls):
            coords2, _, id_line2, bl2, id_reg2 = tls[num_tl-1]
            if id_reg2 == id_reg:
                line_img2 = crop_cv2(img, coords2, Hmin, Wmin, args, bl2)
        check = check_size(coords, Hmin, Wmin)
        if not check:
            print(f"not used {id_line}")
            continue
        # print(num_tl)
        line_img = crop_cv2(img, coords, Hmin, Wmin, args, bl)
        if line_img2 is not None:
            coords = np.array(coords)
            coords2 = np.array(coords2)
            sum_h = line_img.shape[1] + line_img2.shape[1]  + args.line_Sep
            sum_w = max(line_img.shape[0], line_img2.shape[0])
            image_line = np.zeros((sum_w,sum_h , 3))
            # print(line_img.shape, line_img2.shape)
            image_line[0:line_img2.shape[0],0:line_img2.shape[1],:] = line_img2
            image_line[0:line_img.shape[0],line_img2.shape[1]+args.line_Sep:,:] = line_img
            # print(image_line.shape)
            # exit()
            line_img = image_line.astype(np.uint8)
            
        if args.normalized_grayscale:
            # Normalized
            line_img = cv2.cvtColor(line_img, cv2.COLOR_BGR2GRAY)
            # line_img = ( line_img - line_img.min())/( line_img.max() - line_img.min())
            line_img = (line_img - np.mean(line_img)) / np.std(line_img)
            # line_img = cv2.normalize(line_img, None, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_32F)
            height, width = line_img.shape
        elif args.grayscale:
            # Normalized
            
            line_img = cv2.cvtColor(line_img, cv2.COLOR_BGR2GRAY)          
            height, width = line_img.shape
        else:
            height, width, channels = line_img.shape
        fname_img_line = os.path.join(dest_img, "{}.{}.png".format(basename, id_line))
        
        if height == 0 or width == 0:
            print("error ", fname_img_line)
        if args.rotate:
            # print(coords)
            orientation = get_orientation_bl(coords)
            # print(orientation)
            if orientation == "v":
                print(id_line, orientation, args.angle_rot)
                line_img = ndimage.rotate(line_img, args.angle_rot)
        print(line_img.shape)
        cv2.imwrite(fname_img_line, line_img)
        line_img = None

def get_orientation_bl(bl):
        def angle(linea):
            return math.degrees(math.atan2(linea[1][1]-linea[0][1], linea[1][0]-linea[0][0]))
        if bl is None or len(bl) == 0:
            return "h"
        angle_ = abs(angle(bl))
        if 0 <= angle_ <= 45 or 315 <= angle_ <= 360:
            return "h"
        return "v"

def make_page_txt(fname, txts, path_out, Hmin, Wmin, args, line_set):
    page = TablePAGE(im_path=fname)
    tls = page.get_textLines()
    basename = ".".join(fname.split(".")[:-1])
    basename = basename.split("/")[-1]
    n_deleted = 0
    for coords, text, id_line, bl in tls:
        fname_line = "{}.{}".format(basename, id_line)
        check = check_size(coords, Hmin, Wmin, fname_line)
        # if "52681_001.line_1525315515070_1538" in fname_line:
        #      print(text, check)
        if not check:
            # print(fname_line)
            n_deleted += 1
            continue
        text = create_text(text, args)
        # fname_line = os.path.join(path_out, "{}".format(id_line))

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
    for fname in files:
        make_page_img(fname, path_out, dest_img, ext, Hmin, Wmin, args)
    # if args.do_img:
    #     pool = multiprocessing.Pool(processes=n_hilos)              # start 4 worker processes
    #     for fname in files:
    #         pool.apply_async(make_page_img, [fname, path_out, dest_img, ext, Hmin, Wmin, args])
    #     pool.close()
    #     pool.join()
    """
    Print the file with trans
    """
    print("Lines done")
    # Text
    n_deleted = 0
    line_set = set()
    for fname in files:
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
    parser.add_argument('--relative_to_bl', type=str2bool, nargs='?',
                        const=True, default=False,)
    parser.add_argument('--height_from_baseline', type=int, default=128)
    parser.add_argument('--bot_relative_px', type=int, default=10)
    parser.add_argument('--top_relative_px', type=int, default=10)
    parser.add_argument('--min_rel_height_top', type=int, default=8)
    parser.add_argument('--min_rel_height_bot', type=int, default=8)
    parser.add_argument('--max_rel_height_top', type=int, default=8)
    parser.add_argument('--max_rel_height_bot', type=int, default=8)
    args = parser.parse_args()
    print("do_img - ", args.do_img)
    start(args)
