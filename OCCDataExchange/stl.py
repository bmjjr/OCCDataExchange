#!/usr/bin/env python
# coding: utf-8

r"""STL module of OCCDataExchange"""

from __future__ import print_function

import logging

from OCC import StlAPI
from OCC import TopoDS
from OCC.BRepMesh import BRepMesh_IncrementalMesh
from OCCDataExchange.checks import check_importer_filename, check_exporter_filename, check_overwrite, check_shape
from OCCDataExchange.extensions import stl_extensions

logger = logging.getLogger(__name__)


class StlImporter(object):
    r"""STL importer

    Parameters
    ----------
    filename : str

    """

    def __init__(self, filename):
        logger.info("StlImporter instantiated with filename : %s" % filename)

        check_importer_filename(filename, stl_extensions)
        self._filename = filename
        self._shape = None

        logger.info("Reading file ....")
        self.read_file()

    def read_file(self):
        r"""Read the STL file and stores the result in a TopoDS_Shape"""
        stl_reader = StlAPI.StlAPI_Reader()
        shape = TopoDS.TopoDS_Shape()
        stl_reader.Read(shape, self._filename)
        self._shape = shape

    @property
    def shape(self):
        r"""Shape"""
        if self._shape.IsNull():
            raise AssertionError("Error: the shape is NULL")
        else:
            return self._shape


class StlExporter(object):
    """ A TopoDS_Shape to STL exporter. Default mode is ASCII

    Parameters
    ----------
    :param: filename: str
    :param: ascii_mode : bool (default is False)
    :param: line_deflection: float: default 0.9: linear deflection for meshing
        the shape (default is 0.9)
    :param: is_relative: bool: default False: if True deflection used for
        discretization of each edge will be <line_deflection> * <size of edge>.
        Deflection used for the faces will be the maximum deflection of their
        edges.
    :param: angular_deflection: float: default 0.5
    :param: in_parallel: bool: default False: if True shape will be meshed
        in parallel

    """

    def __init__(self, filename=None, ascii_mode=False, line_deflection=0.9,
                 is_relative=False, angular_deflection=0.5, in_parallel=False):
        logger.info("StlExporter instantiated with filename : %s" % filename)
        logger.info("StlExporter ascii : %s" % str(ascii_mode))

        check_exporter_filename(filename, stl_extensions)
        check_overwrite(filename)

        self._shape = None  # only one shape can be exported
        self._ascii_mode = ascii_mode
        self._filename = filename
        self._line_deflection = line_deflection
        self._is_relative = is_relative
        self._angular_deflection = angular_deflection
        self._in_parallel = in_parallel

    def set_shape(self, a_shape):
        """
        only a single shape can be exported...

        Parameters
        ----------
        a_shape

        """
        check_shape(a_shape)  # raises an exception if the shape is not valid
        self._shape = a_shape

    def write_file(self):
        r"""Write file"""
        mesh = BRepMesh_IncrementalMesh(
            self._shape, self._line_deflection, self._is_relative,
            self._angular_deflection, self._in_parallel)
        mesh.Perform()
        stl_writer = StlAPI.StlAPI_Writer()
        stl_writer.SetASCIIMode(self._ascii_mode)
        stl_writer.Write(self._shape, self._filename)
        logger.info("Wrote STL file")
