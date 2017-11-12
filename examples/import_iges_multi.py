#!/usr/bin/env python
# coding: utf-8

r"""Importing multiple shapes from IGES"""

from __future__ import print_function

import logging

from OCC.Display import SimpleGui
from OCCUtils.Topology import Topo

from OCCDataExchange.iges import IgesImporter
from OCCDataExchange.utils import path_from_file

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s :: %(levelname)6s :: %(module)20s :: %(lineno)3d :: %(message)s')
display, start_display, add_menu, add_function_to_menu = SimpleGui.init_display()

# my_iges_importer = occaddons.dataexchange.iges.IgesImporter("../../data/IGES/splines.igs")
filename = path_from_file(__file__, "./models_in/iges/2_boxes.igs")
iges_importer = IgesImporter(filename)

the_shapes = iges_importer.shapes

print(iges_importer.nb_shapes)  # 13
print(len(iges_importer.shapes))  # 13

# display.DisplayShape(iges_importer.compound)

# there are no shells or solids in the compound (IGES specific)

for fc in Topo(iges_importer.compound).faces():
    display.DisplayShape(fc)

display.FitAll()
display.View_Iso()
start_display()
