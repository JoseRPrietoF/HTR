import editdistance
import re, os, glob
import numpy as np 
from page import PAGE

hyp_text = "/home/jose/transcripciones/alcar/nesle/work_acts5/hyp/te_ctc_word.txt"
page_gts = "/data2/LITIS/DAN/Datasets/raw/ALCAR/test/page/"
cer_line_max = 0.1
remove_chars =  ['ⓘ', 'Ⓘ', 'ⓜ', 'Ⓜ', 'ⓕ', 'Ⓕ', 'ⓒ', 'Ⓒ']

save_all = "EvalE2EHTR/nesle"

def create_dir(p:str):
    if not os.path.exists(p):
        os.mkdir(p)

def format_string_for_cer(str):
    """
    Format string for CER computation: remove layout tokens and extra spaces
    """
    str = re.sub('([\n])+', "\n", str)  # remove consecutive line breaks
    str = re.sub('([ ])+', " ", str).strip()  # remove consecutive spaces
    return str

def edit_cer_from_string(gt, pred):
    """
    Format and compute edit distance between two strings at character level
    """
    # gt = format_string_for_cer(gt)
    # pred = format_string_for_cer(pred)
    return editdistance.eval(gt, pred)

def read_text(file:str, remove_chars=[]):
    f = open(file, "r")
    lines = f.readlines()
    f.close()
    res = {}
    for line in lines:
        line = format_string_for_cer(line)
        id_line, *text = line.split(" ")
        text = " ".join(text)
        for c in remove_chars:
            text = text.replace(c, "")
        res[id_line] = text
    return res

def get_pages(path_gts_pages:str, read_text:dict):
    xmls = glob.glob(os.path.join(path_gts_pages, "*xml"))
    pages_GT = []
    pages_HYP = []
    names = []
    for xml in xmls:
        fname = xml.split("/")[-1].split(".")[0]
        names.append(fname)
        page = PAGE(xml)
        acts = page.get_textRegions()
        page_text_gt, page_text_hyp = [], []
        for coords, id_, region in acts:
            tls = page.get_text_lines_from(region)
            for coords_tl, text_tl, id_tl in tls:
                name_id = f"{fname}.{id_tl}"
                page_text_gt.append(text_tl)
                page_text_hyp.append(read_text[name_id])
        pages_GT.append(page_text_gt)
        pages_HYP.append(page_text_hyp)
    return pages_GT, pages_HYP, names

def main(hyp_text, gt_pages, remove_chars):
    create_dir(save_all)
    hyp_text = read_text(hyp_text, remove_chars)
    page_text_gt, page_text_hyp, names = get_pages(gt_pages, hyp_text)
    cers = []
    for gt, hyp, name_page in zip(page_text_gt, page_text_hyp, names):
        # print(gt)
        gt = " ".join(gt)
        hyp = " ".join(hyp)
        cer_line = edit_cer_from_string(gt, hyp) / len(gt)
        print(cer_line)
        # if cer_line > cer_line_max:
        #     print(gt)
        #     print("*")
        #     print(hyp)
        #     print("-------------")
        cers.append(cer_line)
        file_hyp = open(os.path.join(save_all, name_page+".hyp"), "w")
        file_hyp.write(hyp)
        file_hyp.close()
        file_gt = open(os.path.join(save_all, name_page+".ref"), "w")
        file_gt.write(gt)
        file_gt.close()
    print(f"Mean CER {np.mean(cers)}")

if __name__ == "__main__":
    main(hyp_text, page_gts, remove_chars)