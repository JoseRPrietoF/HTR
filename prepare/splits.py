from __future__ import absolute_import
import glob, os, copy, pickle, argparse, random

def get_all_xml(path, ext="xml"):
    file_names = glob.glob(os.path.join(path, "*{}".format(ext)))
    return file_names

def create_dir(p):
    if not os.path.exists(p):
        os.mkdir(p)

def do_splits(args):
    xmls_list = get_all_xml(args.path_input)
    path_out_tr = os.path.join(args.path_out, "tr_data")
    path_out_dev = os.path.join(args.path_out, "dev_data")
    create_dir(args.path_out)
    create_dir(path_out_tr)
    create_dir(path_out_dev)
    num_dev = int(len(xmls_list)*args.dev_split)
    dev_list = random.sample(xmls_list, num_dev)
    tr_list = [x for x in xmls_list if x not in dev_list]
    print("{} for tr and {} for dev - {} Total".format(len(tr_list), len(dev_list), len(xmls_list)))
    for fname in tr_list:
        basename = ".".join(fname.split(".")[:-1])
        basename = basename.split("/")[-1]
        img_path = "{}.{}".format(basename, args.ext_images)
        img_path_abs = os.path.join(args.path_input, img_path)
        path_file_xml_dest = os.path.join(path_out_tr, basename+".xml")
        path_file_img_dest = os.path.join(path_out_tr, img_path)
        os.symlink(fname, path_file_xml_dest)
        os.symlink(img_path_abs, path_file_img_dest)
    for fname in dev_list:
        basename = ".".join(fname.split(".")[:-1])
        basename = basename.split("/")[-1]
        img_path = "{}.{}".format(basename, args.ext_images)
        img_path_abs = os.path.join(args.path_input, img_path)
        path_file_xml_dest = os.path.join(path_out_dev, basename+".xml")
        path_file_img_dest = os.path.join(path_out_dev, img_path)
        os.symlink(fname, path_file_xml_dest)
        os.symlink(img_path_abs, path_file_img_dest)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process lines.')
    parser.add_argument('--path_input', metavar='path_input', type=str,
                    help='Input path where are the xmls and images')
    parser.add_argument('--dev_split', metavar='angle_rot', type=float, 
                    help='Percentatge of the spñit', default=0.1)
    parser.add_argument('--ext_images', metavar='ext_images', type=str,
                    help='Extension of the images. jpg, png, etc', default="jpg")
    parser.add_argument('--path_out', metavar='path_out', type=str,
                    help='Output path to store the results. The dir will be created if doesnt exist')
    args = parser.parse_args()
    do_splits(args)