# -*- coding: utf-8 -*-
#
#
# TheVirtualBrain-Framework Package. This package holds all Data Management, and 
# Web-UI helpful to run brain-simulations. To use it, you also need do download
# TheVirtualBrain-Scientific Package (for simulators). See content of the
# documentation-folder for more details. See also http://www.thevirtualbrain.org
#
# (c) 2012-2013, Baycrest Centre for Geriatric Care ("Baycrest")
#
# This program is free software; you can redistribute it and/or modify it under 
# the terms of the GNU General Public License version 2 as published by the Free
# Software Foundation. This program is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public
# License for more details. You should have received a copy of the GNU General 
# Public License along with this program; if not, you can download it here
# http://www.gnu.org/licenses/old-licenses/gpl-2.0
#
#

'''
.. moduleauthor:: Calin Pavel
'''
import os
import numpy
import shutil
import zipfile
import tempfile
from tvb.basic.traits.util import read_list_data
from tvb.basic.config.settings import TVBSettings as cfg
from tvb.core.adapters.abcadapter import ABCSynchronous
from tvb.core.adapters.exceptions import LaunchException
from tvb.basic.logger.builder import get_logger
from tvb.datatypes.surfaces import RegionMapping, CorticalSurface
from tvb.datatypes.connectivity import Connectivity
from tvb.core.entities.file.fileshelper import FilesHelper

class RegionMapping_Importer(ABCSynchronous):
    """
    Upload RegionMapping from a TXT, ZIP or BZ2 file.
    """ 
    _ui_name = "RegionMapping"
    _ui_subsection = "region_mapping_importer"
    _ui_description = "Import a Region Mapping (Surface - Connectivity) from TXT/ZIP/BZ2"
         
    def __init__(self):
        ABCSynchronous.__init__(self)
        self.logger = get_logger(self.__class__.__module__)

    def get_input_tree(self):
        """
        Define input parameters for this importer.
        """
        return [{'name': 'mapping_file', 'type': 'upload', 'required_type':'', 
                 'label': 'Please upload region mapping file (txt, zip or bz2 format)', 'required': True,
                 'description': 'Expected a text/zip/bz2 file containing region mapping values.' },
                
                {'name': 'surface', 'label': 'Brain Surface', 
                 'type' : CorticalSurface, 'required':True, 'datatype': True,
                 'description': 'The Brain Surface used by uploaded region mapping.'},
                
                {'name': 'connectivity', 'label': 'Connectivity', 
                 'type' : Connectivity, 'required':True, 'datatype': True,
                 'description': 'The Connectivity used by uploaded region mapping.'}
                ]
                             
    def get_output(self):
        return [RegionMapping]

    def get_required_memory_size(self, **kwargs):
        """
        Return the required memory to run this algorithm.
        """
        # Don't know how much memory is needed.
        return -1
    
    def get_required_disk_size(self, **kwargs):
        """
        Returns the required disk size to be able to run the adapter.
        """
        return 0
    
    def launch(self, mapping_file, surface, connectivity):
        """
        Creates region mapping from uploaded data.
        """
        if mapping_file is None:
            raise LaunchException ("Please select mappings file which contains data to import")
        if surface is None:
            raise LaunchException("No surface selected. Please initiate " 
                                  + "upload again and select a brain surface.")
        if connectivity is None:
            raise LaunchException("No connectivity selected. Please initiate " 
                                  + "upload again and select one.")
            
        self.logger.debug("Reading mappings from uploaded file")
        array_data = None
        if zipfile.is_zipfile(mapping_file):
            tmp_folder = tempfile.mkdtemp(prefix='region_mapping_zip_', 
                                          dir=cfg.TVB_TEMP_FOLDER)
            try:
                files = FilesHelper().unpack_zip(mapping_file, tmp_folder)
                if len(files) > 1:
                    raise LaunchException("Please upload a ZIP file containing only one file.")
                array_data = read_list_data(files[0], dtype=numpy.int32)    
            finally:
                if os.path.exists(tmp_folder):
                    shutil.rmtree(tmp_folder)
        else:
            array_data = read_list_data(mapping_file, dtype=numpy.int32)
        
        # Now we do some checks before building final RegionMapping
        if array_data is None or len(array_data) == 0:
            raise LaunchException("Uploaded file does not contains any data." 
                                  + " Please initiate upload with another file.")    
        
        # Check if we have a mapping for each surface vertex.
        if len(array_data) != surface.number_of_vertices:
            msg = ("Imported file contains a different number of values " + 
                  "than the number of surface vertices. " +  
                  "Imported: %d values while surface has: %d vertices.")
            msg = msg%(len(array_data), surface.number_of_vertices)
            raise LaunchException(msg)     
        
        # Now check if the values from imported file correspond to connectivity regions
        if array_data.min() < 0:
            raise LaunchException("Imported file contains negative values. Please fix problem and re-import file")
        
        if array_data.max() >= connectivity.number_of_regions:
            msg = ("Imported file contains invalid regions. Found region: %d while selected " + 
                   "connectivity has: %d regions defined (0 based).")
            msg = msg%(array_data.max(), connectivity.number_of_regions)
            raise LaunchException(msg)
        
        self.logger.debug("Creating RegionMapping instance")
        region_mapping_inst = RegionMapping()
        region_mapping_inst.storage_path = self.storage_path
        region_mapping_inst.set_operation_id(self.operation_id)
        region_mapping_inst.surface = surface
        region_mapping_inst.connectivity = connectivity
        
        if array_data is not None:
            region_mapping_inst.array_data = array_data
        
        return [region_mapping_inst]
    
    