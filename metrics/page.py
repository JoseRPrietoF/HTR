import glob, os, copy, pickle
from xml.dom import minidom
import numpy as np
import os
import sys
import shutil
# import shapely
# from shapely.geometry import LineString, Point

class PAGE():
    """
    Class for parse Tables from PAGE
    """

    def __init__(self, im_path, debug=False,
                 search_on=["TextLine"]):
        """
        Set filename of inf file
        example : AP-GT_Reg-LinHds-LinWrds.inf
        :param fname:
        """
        self.im_path = im_path
        self.DEBUG_ = debug
        self.search_on = search_on

        self.parse()



    def get_daddy(self, node, searching="TextRegion"):
        while node.parentNode:
            node = node.parentNode
            if node.nodeName.strip() == searching:
                return node

    def get_text(self, node, nodeName="Unicode"):
        TextEquiv = None
        for i in node.childNodes:
            if i.nodeName == 'TextEquiv':
                TextEquiv = i
                break
        if TextEquiv is None:
            # print("No se ha encontrado TextEquiv en una región")
            return None

        for i in TextEquiv.childNodes:
            if i.nodeName == nodeName:
                try:
                    words = i.firstChild.nodeValue
                except:
                    words = ""
                return words

        return None

    def get_TableRegion(self, ):
        """
        Return all the cells in a PAGE
        :return: [(coords, col, row)], dict, dict
        """
        cells = []
        for region in self.xmldoc.getElementsByTagName("TableRegion"):
            coords = self.get_coords(region)
            cells.append(coords)

        return cells

    def get_cells(self, ):
        """
        Return all the cells in a PAGE
        :return: [(coords, col, row)], dict, dict
        """
        cells = []
        cell_by_row = {}
        cell_by_col= {}
        for region in self.xmldoc.getElementsByTagName("TableCell"):
            #TODO different tables
            coords = self.get_coords(region)

            row = int(region.attributes["row"].value)
            col = int(region.attributes["col"].value)
            cells.append((coords, col, row))

            cols = cell_by_col.get(col, [])
            cols.append(coords)
            cell_by_col[col] = cols

            rows = cell_by_row.get(row, [])
            rows.append(coords)
            cell_by_row[row] = rows
        return cells, cell_by_col, cell_by_row

    def get_Baselines(self, ):
        """
        A partir de un elemento del DOM devuelve, para cada textLine, sus coordenadas y su contenido
        :param dom_element:
        :return: [(coords, words)]
        """
        text_lines = []
        for region in self.xmldoc.getElementsByTagName("Baseline"):
            coords = region.attributes["points"].value
            coords = coords.split()
            coords_to_append = []
            for c in coords:
                x, y = c.split(",")
                coords_to_append.append((int(x), int(y)))

            text_lines.append(coords_to_append)


        return text_lines

    def get_textLines_normal(self, ):
        """
        A partir de un elemento del DOM devuelve, para cada textLine, sus coordenadas y su contenido
        :param dom_element:
        :return: [(coords, words)]
        """
        text_lines = []
        for region in self.xmldoc.getElementsByTagName("TextLine"):
            coords = self.get_coords(region)
            text = self.get_text(region)
            
            text_lines.append((coords, text))

        return text_lines

    def get_textLines(self, bbox:list, min=0.3):
        """
        A partir de un elemento del DOM devuelve, para cada textLine, sus coordenadas y su contenido solo si esta dentro del Bbox dado
        :param dom_element:
        :return: [(coords, words)]
        """
        text_lines = []
        for region in self.xmldoc.getElementsByTagName("TextLine"):
            coords = self.get_coords(region)
            text = self.get_text(region)
            coords = get_bbox(coords) # xmin, ymin, xmax, ymax
            overlap_line = overlappingArea(bbox, coords)
            if overlap_line > min:
                # print(coords, text, overlap_line)
                text_lines.append((coords, text))
            # else:
            #     print('****', coords, text, overlap_line)
        # print(len(text_lines))
        return text_lines


    def get_textLines_byType(self, type="$tip"):
        """
        A partir de un elemento del DOM devuelve, para cada textLine, sus coordenadas y su contenido
        :param dom_element:
        :return: [(coords, words)]
        """
        text_lines = []
        for region in self.xmldoc.getElementsByTagName("TextLine"):
            type_tl = region.attributes["custom"].value
            if "$tip" in type_tl:
                coords = self.get_coords(region)
                text = self.get_text(region)

                text_lines.append((coords, text))


        return text_lines

    def get_minium_line_byType(self, type="$tip"):
        """
        Devuelve las lineas de cada TextRegion del tipo que se busca.
        :param dom_element:
        :return: [(coords, words)]
        """
        text_lines = []
        for region in self.xmldoc.getElementsByTagName("TextRegion"):
            type_tl = region.attributes["custom"].value
            if "$tip" in type_tl:
                coords_aux = []
                for child in region.childNodes:
                    # type TextLine?
                    if child.nodeName == 'TextLine':
                        coords = self.get_coords(child)
                        coords_aux.extend(coords)

                text_lines.append(coords_aux)

        return text_lines


    def get_textRegions(self, ):
        """
        A partir de un elemento del DOM devuelve, para cada textregion, sus coordenadas y su id
        :param dom_element:
        :return: [(coords, id)]
        """
        text_lines = []
        for region in self.xmldoc.getElementsByTagName("TextRegion"):
            coords = self.get_coords(region)
            id = region.attributes["id"].value if 'id' in region.attributes else None

            text_lines.append((coords, id, region))
        return text_lines
    
    def get_textRegionsActs(self, max_iou=1.0):
        """
        A partir de un elemento del DOM devuelve, para cada textregion, sus coordenadas y su id
        :param dom_element:
        :return: [(coords, id)]
        """
        text_lines = []
        for region in self.xmldoc.getElementsByTagName("TextRegion"):
            coords = self.get_coords(region)
            id_act = region.attributes["id"].value
            custom = region.attributes["custom"].value # structure {type:AC;}
            probs = region.attributes["probs"].value.split(";")
            probs = {pp.split(":")[0]:float(pp.split(":")[1]) for pp in probs if pp}
            type_, probBbox, probType, _ = custom.split(";")
            type_ = type_.split("type:")[-1]
            probBbox = float(probBbox.split("probBbox:")[-1])
            probType = float(probType.split("probType:")[-1])
            coords = np.array(coords)
            text_lines.append((coords, id_act, region, {"type":type_, "probBbox":probBbox, "probType":probType, "probs":probs}))
            # print(coords)
        final_list = []
        coords_used = set()
        # print(len(text_lines))
        for i, (coords, id_act, region, info) in enumerate(text_lines):
            if i in coords_used:
                continue
            for j in range(i+1, len(text_lines)):
                coords2, id_act2, region2, info2 = text_lines[j]
                iou = bb_intersection_over_union(coords, coords2)
                # print("----", coords, coords2, iou)
                if iou > max_iou and i not in coords_used:
                    final_list.append((coords, id_act, region, info))
                    coords_used.add(i)
                    coords_used.add(j)
            if i not in coords_used:
                final_list.append((coords, id_act, region, info))
                coords_used.add(i)
        return final_list
    

    def get_text_lines_from(self, dom_element):
        """
        A partir de un elemento del DOM devuelve, para cada textLine, sus coordenadas y su contenido
        :param dom_element:
        :return: [(coords, words)]
        """
        text_lines = []
        for i in dom_element.childNodes:
            if i.nodeName != 'TextLine':
                continue
            coords = self.get_coords(i)
            coords = get_bbox_from_coords(coords)
            text = self.get_text(i)
            id = i.attributes["id"].value

            text_lines.append((coords, text, id))


        return text_lines

    def get_textRegions_all(self, ):
        """
        A partir de un elemento del DOM devuelve, para cada textregion, sus coordenadas y su id
        :param dom_element:
        :return: [(coords, id)]
        """
        text_lines = []
        for region in self.xmldoc.getElementsByTagName("TextRegion"):
            coords = self.get_coords(region)
            coords = get_bbox_from_coords(coords)
            id = region.attributes["id"].value if 'id' in region.attributes else None
            # "readingOrder {index:0;} structure {type:notice;}
            type_ = region.attributes["custom"].value.split("type:")[-1].split(";")[0].lower()

            lines = self.get_text_lines_from(region)

            text_lines.append((coords, id, lines, type_))
        return text_lines

    def get_coords(self, dom_element):
        """
        Devuelve las coordenadas de un elemento. Coords
        :param dom_element:
        :return: ((pos), (pos2), (pos3), (pos4)) es un poligono. Sentido agujas del reloj
        """
        coords_element = None
        for i in dom_element.childNodes:
            if i.nodeName == 'Coords':
                coords_element = i
                break
        if coords_element is None:
            print("No se ha encontrado coordenadas en una región")
            return None

        coords = coords_element.attributes["points"].value
        coords = coords.split()
        coords_to_append = []
        for c in coords:
            x, y = c.split(",")
            coords_to_append.append((int(x), int(y)))
        return coords_to_append

    def parse(self):
        self.xmldoc = minidom.parse(self.im_path)

    def get_width(self):
        page = self.xmldoc.getElementsByTagName('Page')[0]
        return int(page.attributes["imageWidth"].value)

    def get_height(self):
        page = self.xmldoc.getElementsByTagName('Page')[0]
        return int(page.attributes["imageHeight"].value)

    def get_image_name_file(self):
        page = self.xmldoc.getElementsByTagName('Page')[0]
        return page.attributes["imageFilename"].value

def area(a, b):  # returns None if rectangles don't intersect
    dx = min(a[2], b[2]) - max(a[0], b[0])
    dy = min(a[3], b[3]) - max(a[1], b[1])
    if (dx>=0) and (dy>=0):
        return dx*dy
    return 0

def overlappingArea(bbox1, line):
    # PFind total area of two
    # overlapping Rectangles
    # Returns Total Area  of two overlap
    #  rectangles
    # l1 = [bbox1[0], bbox1[1]]
    # r1 = [bbox1[2], bbox1[3]]
    # l2 = [line[0], line[1]]
    # r2 = [line[2], line[3]]
    area_comun = area(bbox1, line)
    # print(f'area(bbox1, line) {area_comun}')
    r1 = [bbox1[0], bbox1[3]]
    l1 = [bbox1[2], bbox1[1]]
    r2 = [line[0], line[3]]
    l2 = [line[2], line[1]]
    x = 0
    y = 1
 
    # Area of 2nd Rectangle
    line_area = abs(l2[x] - r2[x]) * abs(l2[y] - r2[y])
 
    return area_comun / line_area

def get_bbox(contours):
    contours = np.squeeze(contours)
    xmax ,xmin = np.max([ x[0] for x in contours]), np.min([ x[0] for x in contours])
    ymax ,ymin = np.max([ x[1] for x in contours]), np.min([ x[1] for x in contours])
    return [xmin, ymin, xmax, ymax]

def bb_intersection_over_union(boxA, boxB):
    # determine the (x, y)-coordinates of the intersection rectangle
    maxy_A = np.max(boxA[:,1])
    miny_A = np.min(boxA[:,1])
    maxx_A = np.max(boxA[:,0])
    minx_A = np.min(boxA[:,0])
    boxA = [minx_A, miny_A, maxx_A, maxy_A]

    maxy_B = np.max(boxB[:,1])
    miny_B = np.min(boxB[:,1])
    maxx_B = np.max(boxB[:,0])
    minx_B = np.min(boxB[:,0])
    boxB = [minx_B, miny_B, maxx_B, maxy_B]

    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    # compute the area of intersection rectangle
    interArea = (xB - xA) * (yB - yA)

    # compute the area of both the prediction and ground-truth
    # rectangles
    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])

    # compute the intersection over union by taking the intersection
    # area and dividing it by the sum of prediction + ground-truth
    # areas - the interesection area
    iou = interArea / float(boxAArea + boxBArea - interArea)

    # return the intersection over union value
    return iou

def get_bbox_from_coords(coords:list):
    coords = np.array(coords)
    min_x = np.min(coords[:,0])
    max_x = np.max(coords[:,0])
    min_y = np.min(coords[:,1])
    max_y = np.max(coords[:,1])
    return min_x, min_y, max_x, max_y