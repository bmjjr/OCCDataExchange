#!/usr/bin/env python
# coding: utf-8

r"""step_ocaf module of OCCDataExchange"""

from __future__ import print_function

import logging

from OCC import IFSelect
from OCC import Quantity
from OCC import STEPCAFControl
from OCC import STEPControl
from OCC import TCollection
from OCC import TDF
from OCC import TDocStd
from OCC import TopAbs
from OCC import XCAFApp
from OCC import XCAFDoc
from OCC import XSControl
from OCCUtils.Topology import Topo

from OCCDataExchange.checks import check_importer_filename, check_exporter_filename, check_overwrite, check_shape
from OCCDataExchange.extensions import step_extensions

logger = logging.getLogger(__name__)


class StepOcafImporter(object):
    r"""Imports STEP file that support layers & colors"""

    def __init__(self, filename):

        check_importer_filename(filename, step_extensions)

        self.filename = filename

        # The shape at index i in the following list corresponds
        # to the color and layer at index i in their respective lists
        self._shapes = list()
        self._colors = list()
        self._layers = list()

        self.read_file()

    @property
    def shapes(self):
        r"""Shapes"""
        return self._shapes

    @property
    def colors(self):
        r"""Colors"""
        return self._colors

    @property
    def layers(self):
        r"""Layers"""
        return self._layers

    @property
    def layers_str(self):
        r"""Returns a readable list of layers in the same order as self._shapes

        If self.shapes = [shape_1, shape_2], layers_str will return ['red', 'green'] when shape_1 is on the "red" layer
        and shape_2 is on the 'green' layer.

        See Also
        --------
        examples/export_multi_to_step_colors_layers_ocaf.py

        """
        layer_string_list = list()
        for i, layer in enumerate(self._layers):
            string = ""
            for j in range(1, layer.GetObject().Length() + 1):
                extended_string = layer.GetObject().Value(j)

                for k in range(1, extended_string.Length() + 1):
                    ascii_code = extended_string.Value(k)
                    string += (chr(ascii_code))

            layer_string_list.append(string)
        return layer_string_list

    def read_file(self):
        r"""Read file"""
        logger.info("Reading STEP file")
        h_doc = TDocStd.Handle_TDocStd_Document()

        # Create the application
        app = XCAFApp._XCAFApp.XCAFApp_Application_GetApplication().GetObject()
        app.NewDocument(TCollection.TCollection_ExtendedString("MDTV-CAF"), h_doc)

        # Get root assembly
        doc = h_doc.GetObject()
        h_shape_tool = XCAFDoc.XCAFDoc_DocumentTool().ShapeTool(doc.Main()).GetObject()
        color_tool = XCAFDoc.XCAFDoc_DocumentTool().ColorTool(doc.Main()).GetObject()
        layer_tool = XCAFDoc.XCAFDoc_DocumentTool().LayerTool(doc.Main()).GetObject()
        l_materials = XCAFDoc.XCAFDoc_DocumentTool().MaterialTool(doc.Main()).GetObject()

        step_reader = STEPCAFControl.STEPCAFControl_Reader()
        step_reader.SetColorMode(True)
        step_reader.SetLayerMode(True)
        step_reader.SetNameMode(True)
        step_reader.SetMatMode(True)

        status = step_reader.ReadFile(self.filename)

        if status == IFSelect.IFSelect_RetDone:
            logger.info("Transfer doc to STEPCAFControl_Reader")
            step_reader.Transfer(doc.GetHandle())
        else:
            raise ValueError("could not read {}".format(self.filename))

        labels = TDF.TDF_LabelSequence()
        color_labels = TDF.TDF_LabelSequence()
        # TopoDS_Shape a_shape;
        h_shape_tool.GetFreeShapes(labels)
        h_shape_tool.GetShapes(labels)

        logger.info('Number of shapes at root :%i' % labels.Length())

        # for i in range(labels.Length()):
        #     a_shape = h_shape_tool.GetObject().GetShape(labels.Value(i+1))
        #     logger.debug("%i - type : %s" % (i, a_shape.ShapeType()))
        #     sub_shapes_labels = TDF.TDF_LabelSequence()
        #     print("Is Assembly?", shape_tool.IsAssembly(labels.Value(i + 1)))
        #     # sub_shapes = shape_tool.getsubshapes(labels.Value(i+1), sub_shapes_labels)
        #
        #     sub_shapes = shape_tool.FindSubShape(labels.Value(i + 1), a_shape, labels.Value(i + 1))
        #     print('Number of subshapes in the assembly : %i' % sub_shapes_labels.Length())
        #
        # color_tool.GetObject().GetColors(color_labels)
        # logger.info('Number of colors : %i' % color_labels.Length())

        for i in range(labels.Length()):
            # print i
            label = labels.Value(i + 1)
            logger.debug("Label : %s" % label)
            a_shape = h_shape_tool.GetShape(labels.Value(i + 1))

            # string_seq = TColStd.TColStd_HSequenceOfExtendedString()
            # string_seq is an TColStd.TColStd_HSequenceOfExtendedString
            string_seq = layer_tool.GetLayers(a_shape)
            color = Quantity.Quantity_Color()
            c = color_tool.GetColor(a_shape, XCAFDoc.XCAFDoc_ColorSurf, color)

            logger.info("The shape type is : %i" % a_shape.ShapeType())
            if a_shape.ShapeType() == TopAbs.TopAbs_COMPOUND:
                logger.info("The shape type is TopAbs.TopAbs_COMPOUND")
                topo = Topo(a_shape)
                logger.info("Nb of compounds : %i" % topo.number_of_compounds())
                logger.info("Nb of solids : %i" % topo.number_of_solids())
                logger.info("Nb of shells : %i" % topo.number_of_shells())
                for solid in topo.solids():
                    logger.info("Adding solid to the shapes list")
                    self._shapes.append(solid)
            elif a_shape.ShapeType() == TopAbs.TopAbs_SOLID:
                logger.info("The shape type is TopAbs.TopAbs_SOLID")
                self._shapes.append(a_shape)
                self._colors.append(color)
                self._layers.append(string_seq)

        return True


class StepOcafExporter(object):
    r"""STEP export that support layers & colors"""

    def __init__(self, filename, layer_name='layer-00'):
        logger.info("StepOcafExporter instantiated with filename : %s" % filename)

        check_exporter_filename(filename, step_extensions)
        check_overwrite(filename)

        self.filename = filename
        self.h_doc = h_doc = TDocStd.Handle_TDocStd_Document()
        logger.info("Empty Doc?", h_doc.IsNull())

        # Create the application
        app = XCAFApp._XCAFApp.XCAFApp_Application_GetApplication().GetObject()
        app.NewDocument(TCollection.TCollection_ExtendedString("MDTV-CAF"), h_doc)

        # Get root assembly
        doc = h_doc.GetObject()
        self.shape_tool = XCAFDoc.XCAFDoc_DocumentTool().ShapeTool(doc.Main()).GetObject()
        self.colors = XCAFDoc.XCAFDoc_DocumentTool().ColorTool(doc.Main()).GetObject()
        self.layers = XCAFDoc.XCAFDoc_DocumentTool().LayerTool(doc.Main()).GetObject()
        labels = TDF.TDF_LabelSequence()
        color_labels = TDF.TDF_LabelSequence()
        # TopoDS_Shape aShape;

        self.top_label = self.shape_tool.NewShape()
        self.current_color = Quantity.Quantity_Color(Quantity.Quantity_NOC_RED)
        self.current_layer = self.layers.AddLayer(TCollection.TCollection_ExtendedString(layer_name))
        self.layer_names = {}

    def set_color(self, r=1, g=1, b=1, color=None):
        r"""Set color

        Parameters
        ----------
        r : float
        g : float
        b : float
        color : Quantity.Quantity_Color

        """
        if color is not None:
            self.current_color = color
        else:
            clr = Quantity.Quantity_Color(r, g, b, 0)
            self.current_color = clr

    def set_layer(self, layer_name):
        r"""set the current layer name

        if the layer has already been set before, that TDF_Label will be used

        Parameters
        ----------
        layer_name: str
            name of the layer

        """
        if layer_name in self.layer_names:
            self.current_layer = self.layer_names[layer_name]
        else:
            self.current_layer = self.layers.AddLayer(TCollection.TCollection_ExtendedString(layer_name))
            self.layer_names[layer_name] = self.current_layer

    def add_shape(self, shape, color=None, layer=None):
        r"""add a shape to export

        a layer and color can be specified.

        note that the set colors / layers will be used for further objects
        added too!

        Parameters
        ----------
        shape : TopoDS_Shape
            the TopoDS_Shape to export
        color :
            can be a tuple: (r,g,b) or a Quantity_Color instance
        layer : str
            layer name

        """
        check_shape(shape)  # raises an exception if the shape is not valid

        shp_label = self.shape_tool.AddShape(shape)

        if color is None:
            self.colors.SetColor(shp_label, self.current_color, XCAFDoc.XCAFDoc_ColorGen)
        else:
            if isinstance(color, Quantity.Quantity_Color):
                self.current_color = color
            else:
                assert len(color) == 3, 'expected a tuple with three values < 1.'
                r, g, b = color
                self.set_color(r, g, b)
            self.colors.SetColor(shp_label, self.current_color, XCAFDoc.XCAFDoc_ColorGen)

        if layer is None:
            self.layers.SetLayer(shp_label, self.current_layer)
        else:
            self.set_layer(layer)
            self.layers.SetLayer(shp_label, self.current_layer)

    def write_file(self):
        r"""Write file"""
        work_session = XSControl.XSControl_WorkSession()
        writer = STEPCAFControl.STEPCAFControl_Writer(work_session.GetHandle(), False)

        transfer_status = writer.Transfer(self.h_doc, STEPControl.STEPControl_AsIs)
        if transfer_status != IFSelect.IFSelect_RetDone:
            msg = "An error occurred while transferring a shape to the STEP writer"
            logger.error(msg)
            raise ValueError(msg)
        logger.info('Writing STEP file')

        write_status = writer.Write(self.filename)
        if write_status == IFSelect.IFSelect_RetDone:
            logger.info("STEP file write successful.")
        else:
            msg = "An error occurred while writing the STEP file"
            logger.error(msg)
            raise ValueError(msg)
