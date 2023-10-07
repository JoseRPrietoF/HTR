from __future__ import absolute_import
import glob, os, copy, pickle
from xml.dom import minidom
import numpy as np, cv2
from page import TablePAGE
import unidecode, re
# from threading import Thread
# from random import random
# import threading
import time, pickle
import multiprocessing
import argparse
from scipy import ndimage
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation

def save_to_file(data, fname):
    with open(fname, 'wb') as handle:
        pickle.dump(data, handle, protocol=pickle.HIGHEST_PROTOCOL)

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

def create_text(line, args):
        res = ""
        line = line.lower()
        if args.passau:
            line = line.replace(" ", "")
            line = line.replace("&lt;space&gt;", " ")
            line = line.replace("&lt;ign&gt;", "")
            line = line.replace("<ign>", "")
            line = line.replace("<space>", " ")
        line = unidecode.unidecode(line)
        line =  re.sub(r"[^a-zA-Z0-9 ]+", '', line)
        line = line.lstrip()
        res = line.lower() 
        # for w in line:
        #     if w == " ":
        #         w = "<space>"
            
        #     res += "{} ".format(w.lower())
        if res == " " or not res or res == "":
            # print("Empty")
            res = "\""
        # line = line.replace(" ", "")
        # line = line.replace("<space>", " ")
        return res

def make_trans(t, args=None):
    t = t.replace(" ", "")
    t = t.replace("<space>", " ")
    return t

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

def make_page_txt(fname, txts, path_out, Hmin, Wmin, args, line_set, path_data):
    page = TablePAGE(im_path=fname)
    tls = page.get_textLinesFromCell()
    """
    tls:
    coords, text, id, {
                'DU_row': DU_row,
                'DU_col': DU_col,
                'DU_header': DU_header,
                'row': row,
                'col': col,
    """
    basename = ".".join(fname.split(".")[:-1])
    basename = basename.split("/")[-1]
    n_deleted = 0
    text_res = []
    # f_Result = open(os.path.join(path_data, basename), "w")
    str_w = "text || #col || #row || type_cell (Outside, Data cell, Col Header) \n"
    # f_Result.write(str_w)
    # print(str_w)
    cols, rows = set(), set()
    for  coords, text, id_line, dict_table_info in tls:
        fname_line = "{}.{}".format(basename, id_line)
        check = check_size(coords, Hmin, Wmin, fname_line)
        # if "52681_001.line_1525315515070_1538" in fname_line:
        #      print(text, check)
        if not check:
            # print(fname_line)
            n_deleted += 1
            continue
        text = create_text(text, args)
        row, col, type_cell = dict_table_info["row"], dict_table_info["col"], dict_table_info["DU_header"]
        # print(text, " |||||||||||||||", translation.text)
        # exit()
        # print(text_res)
        str_w = "{} || {} || {} || {} \n".format(text, col, row, type_cell)
        # print(str_w)
        # f_Result.write(str_w)
        text_res.append(text)
        # fname_line = os.path.join(path_out, "{}".format(id_line))
        cols.add(col)
        rows.add(row)
        if fname_line not in line_set:
            txts.append([fname_line, text])
            line_set.add(fname_line)
    # f_Result.close()
    return n_deleted, text_res, len(cols), len(rows)

def start(args):
    # Settings
    Hmin, Wmin = args.min_size
    # Input
    path = args.path_input
    # Output
    path_out = args.path_out
    result_path = os.path.join(path_out, args.result_path)
    result_path_vocab = os.path.join(path_out, args.result_path_vocab)
    path_data = os.path.join(path_out, "data")
    ##############
    """
    Crop the lines
    """
    create_dir(path_out)
    create_dir(path_data)
    files = get_all_xml(path)
    txts = []

    """
    Print the file with trans
    """
    # Text
    n_deleted = 0
    line_set = set()
    text = []
    total_cols, total_rows = 0, 0
    for fname in files:
        n_del, text_res, ncols, nrows = make_page_txt(fname, txts, path_out, Hmin, Wmin, args, line_set, path_data)
        n_deleted += n_del
        text.extend(text_res)
        total_cols += ncols
        total_rows += nrows
    # print(text)
    # print(len(text))
    print("A total of {} files - {} lines".format(len(files), len(txts)))
    print("Deleted a total of {} lines under H {} and W {}".format(n_deleted, Hmin, Wmin))
    n_components = 40
    max_iters = 10000
    f_Result_topic = open(os.path.join(path_data, "topic_detection_{}topics_{}iters".format(n_components, max_iters )), "w")
    f_Result_words = open(os.path.join(path_data, "topic_detection_words_{}topics_{}iters".format(n_components, max_iters )), "w")
    vectorizer = CountVectorizer()
    X = vectorizer.fit_transform(text)
    lda = LatentDirichletAllocation(n_components = n_components, random_state = 42, max_iter=max_iters)
    lda.fit(X) 
    n_words = 20
    for index, topic in enumerate(lda.components_):
        f_Result_words.write(f'Top {n_words} words for Topic #{index} \n')
        l = " ".join([vectorizer.get_feature_names()[i] for i in topic.argsort()[-n_words:]])
        f_Result_words.write(f'#{index} - {l}')
        f_Result_words.write('\n')
    topic_results = lda.transform(X)
    f_Result_words.close()
    print(topic_results.shape)
    print(topic_results[0])
    print(topic_results[0].argmax())
    argmaxs_topic = topic_results.argmax(axis = 1)
    
    for i, argmax in enumerate(argmaxs_topic ):
        f_Result_topic.write(f'{text[i]} - {argmax} \n')
    f_Result_topic.close()
    save_to_file({
        'vectorizer':vectorizer,
        'lda':lda,
        }, os.path.join(path_data, "models_{}topics_{}iters".format(n_components, max_iters )))
    # topic_word = model.topic_word_
    # n_top_words = 30
    # vocab = vectorizer.get_feature_names()
    # for i, topic_dist in enumerate(topic_word):
    #      topic_words = np.array(vocab)[np.argsort(topic_dist)][:-(n_top_words+1):-1]
    #      print('Topic {}: {}'.format(i, ' '.join(topic_words)))

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
    parser.add_argument('--path_input', metavar='path_input', type=str,
                    help='Input path where are the xmls and images')
    parser.add_argument('--path_out', metavar='path_out', type=str,
                    help='Output path to store the results. The dir will be created if doesnt exist')
    parser.add_argument('--result_path', metavar='result_path', type=str,
                    help='Name of the output file to store the trans. Will be saved in path_out', default="table.txt")
    parser.add_argument('--result_path_vocab', metavar='result_path_vocab', type=str,
                    help='Name of the output file to store the trans. Will be saved in path_out', default="table.txt")
    parser.add_argument('--dir_output_lines', metavar='dir_output_lines', type=str,
                    help='Name of the output dir to store the lines. The dir Will be created in path_out', default="lines")
    parser.add_argument('--min_size', metavar='min_size', type=int, nargs=2,
                    help='Min sizes of Height and Width in pixels[H W]', default=[15, 15])
    parser.add_argument('--passau', type=str2bool, nargs='?',
                        const=True, default=False,)
    args = parser.parse_args()
    # import lda.datasets
    # vocab = lda.datasets.load_reuters_vocab()
    # titles = lda.datasets.load_reuters_titles()
    # print(vocab)
    # print(titles)
    # X = lda.datasets.load_reuters()
    # print(X)
    start(args)
