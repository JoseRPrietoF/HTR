import editdistance
import re
import numpy as np 

gt_text = "/home/jose/transcripciones/alcar/nesle/work_acts5/gt/trans_test.txt"
hyp_text = "/home/jose/transcripciones/alcar/nesle/work_acts5/hyp/te_ctc_word.txt"
cer_line_max = 0.4
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

def read_text(file:str):
    f = open(file, "r")
    lines = f.readlines()
    f.close()
    res = {}
    for line in lines:
        line = format_string_for_cer(line)
        id_line, *text = line.split(" ")
        res[id_line] = " ".join(text)
    return res

def main(gt_text, hyp_text):
    gt = read_text(gt_text)
    hyp = read_text(hyp_text)
    cers = []
    for id_line_gt, text_gt in gt.items():
        text_hyp = hyp[id_line_gt]
        cer_line = edit_cer_from_string(text_gt, text_hyp) / len(text_gt)
        if cer_line > cer_line_max:
            print(f"{id_line_gt} {cer_line}")
            print(text_gt)
            print(text_hyp)
            print("-------------")
        cers.append(cer_line)
    print(f"Mean CER {np.mean(cers)}")

if __name__ == "__main__":
    main(gt_text, hyp_text)