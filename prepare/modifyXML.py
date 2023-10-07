from __future__ import absolute_import
import glob, os
from xml.dom import minidom

def parse(im_path):
    xmldoc = minidom.parse(im_path)
    return xmldoc

def save_changes(fname, xmldoc):
    file = open(fname, 'w')
    file.write(xmldoc.toprettyxml())
    file.close()

def main(path):
    # list_xml = ["/data2/jose/corpus/tablas_DU/icdar_488/52761_010.xml"]
    list_xml = glob.glob(os.path.join(path, "*xml"))
    for xml in list_xml:
        basename = xml.split("/")[-1].split(".")[0]
        xmldoc = parse(xml)
        dom_element_page = xmldoc.getElementsByTagName('Page')[0]
        dom_element_page.attributes['imageFilename'].value = basename
        save_changes(xml, xmldoc)
    print("A total of {} xmls changed in {}".format(len(list_xml), path))



if __name__ == "__main__":
    # path = "/data2/jose/corpus/tablas_DU/icdar_488/"
    path = "/data2/jose/corpus/tablas_DU/icdar19_abp_small"
    # path = "/data2/jose/corpus/tablas_DU/icdar_abp_1098"
    main(path)