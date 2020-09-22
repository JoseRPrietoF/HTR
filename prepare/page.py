from __future__ import absolute_import
import glob, os, copy, pickle
from xml.dom import minidom
import numpy as np

class TablePAGE():
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
        return None

    def get_text(self, node, nodeName="Unicode"):
        TextEquiv = None
        for i in node.childNodes:
            if i.nodeName == 'TextEquiv':
                TextEquiv = i
                break
        if TextEquiv is None:
            print("No se ha encontrado TextEquiv en una región")
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

    def get_cells_with_header(self, ):
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
            DU_Header = "O"
            for child in region.childNodes:
                att = child.attributes
                if att and "DU_header" in list(att.keys()):
                    DU_Header = att["DU_header"].value
                    break
            row = int(region.attributes["row"].value)
            col = int(region.attributes["col"].value)
            cells.append((coords, col, row, DU_Header))

            cols = cell_by_col.get(col, [])
            cols.append(coords)
            cell_by_col[col] = cols

            rows = cell_by_row.get(row, [])
            rows.append(coords)
            cell_by_row[row] = rows

        return cells, cell_by_col, cell_by_row

    def get_Separator(self, vertical=True):
        """
        Return all the GridSeparator in a PAGE (TranskribusDU - ABTTableGrid)
        :return: [(coords, col, row)], dict, dict
        """
        cells = []
        for region in self.xmldoc.getElementsByTagName("SeparatorRegion"):
            # orient_reg = int(region.attributes["orient"])
            orient_reg = "vertical" in region.attributes["orient"].value
            # if orient == orient_reg:
            if vertical == orient_reg :
                coords = self.get_coords(region)
                cells.append(coords)
        return cells

    def get_GridSeparator(self, orient=90):
        """
        Return all the GridSeparator in a PAGE (TranskribusDU - ABTTableGrid)
        :return: [(coords, col, row)], dict, dict
        """
        cells = []
        for region in self.xmldoc.getElementsByTagName("GridSeparator"):
            orient_reg = int(region.attributes["orient"].value)
            # orient_reg = "vertical" in region.attributes["orient"].value
            if orient == orient_reg:
            # if vertical == orient_reg :
                coords = self.get_coords(region)
                cells.append(coords)
        return cells

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



    def get_textLines(self, ):
        """
        A partir de un elemento del DOM devuelve, para cada textLine, sus coordenadas y su contenido
        :param dom_element:
        :return: [(coords, words)]
        """
        text_lines = []
        for region in self.xmldoc.getElementsByTagName("TextLine"):
            id_line = region.attributes["id"].value
            coords = self.get_coords(region)
            text = self.get_text(region)

            text_lines.append((coords, text, id_line))


        return text_lines

    def get_textLinesWithObject(self, ):
        """
        A partir de un elemento del DOM devuelve, para cada textLine, sus coordenadas y su contenido
        :param dom_element:
        :return: [(coords, words)]
        """
        text_lines = []
        for region in self.xmldoc.getElementsByTagName("TextLine"):
            coords = self.get_coords(region)
            text = self.get_text(region)

            text_lines.append((coords, text, region))


        return text_lines

    def get_textLinesFromCell(self, ):
        """
        A partir de un elemento del DOM devuelve, para cada textLine, sus coordenadas y su contenido
        :param dom_element:
        :return: [(coords, words)]
        """
        text_lines = []
        for region in self.xmldoc.getElementsByTagName("TextLine"):
            coords = self.get_coords(region)
            text = self.get_text(region)


            tablecell = self.get_daddy(region, "TableCell")
            DU_row, DU_col, DU_header = region.attributes["DU_row"].value, \
                                        region.attributes["DU_col"].value, \
                                        region.attributes["DU_header"].value



            id = region.attributes["id"].value
            row, col = -1,-1
            if tablecell is not None:
                row, col = int(tablecell.attributes["row"].value), int(tablecell.attributes["col"].value)

            text_lines.append((coords, text, id, {
                'DU_row': DU_row,
                'DU_col': DU_col,
                'DU_header': DU_header,
                'row': row,
                'col': col,
            }))

        return text_lines

    def get_textLinesFromCell(self, ):
        """
        A partir de un elemento del DOM devuelve, para cada textLine, sus coordenadas y su contenido
        :param dom_element:
        :return: [(coords, words)]
        """
        text_lines = []
        for region in self.xmldoc.getElementsByTagName("TextLine"):
            coords = self.get_coords(region)
            text = self.get_text(region)


            tablecell = self.get_daddy(region, "TableCell")
            DU_row, DU_col, DU_header = region.attributes["DU_row"].value, \
                                        region.attributes["DU_col"].value, \
                                        region.attributes["DU_header"].value



            id = region.attributes["id"].value
            row, col = -1,-1
            if tablecell is not None:
                row, col = int(tablecell.attributes["row"].value), int(tablecell.attributes["col"].value)

            text_lines.append((coords, text, id, {
                'DU_row': DU_row,
                'DU_col': DU_col,
                'DU_header': DU_header,
                'row': row,
                'col': col,
            }))

        return text_lines

    def get_textLinesFromCellHisClima(self, width):
        """
        A partir de un elemento del DOM devuelve, para cada textLine, sus coordenadas y su contenido
        :param dom_element:
        :return: [(coords, words)]
        """
        max_width = width*0.4
        text_lines = []
        for region in self.xmldoc.getElementsByTagName("TextLine"):
            coords = self.get_coords(region)
            bl = np.array(coords)
            bb = max(bl[:, 0]) - min(bl[:, 0])
            if bb >= max_width:
                continue
            text = self.get_text(region)


            tablecell = self.get_daddy(region, "TableCell")
            try:
                DU_row, DU_col = region.attributes["row"].value, \
                                            region.attributes["col"].value
            except:
                DU_row = -1
                DU_col = -1



            id = region.attributes["id"].value
            row, col = -1,-1
            if tablecell is not None:
                row, col = int(tablecell.attributes["row"].value), int(tablecell.attributes["col"].value)

            text_lines.append((coords, text, id, {
                'DU_row': DU_row,
                'DU_col': DU_col,
                'row': row,
                'col': col,
            }))

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