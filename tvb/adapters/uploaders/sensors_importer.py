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

"""
Created on Mar 13, 2012

.. moduleauthor:: Bogdan Neacsa <bogdan.neacsa@codemart.ro>
"""
import numpy
from tvb.core import utils
from tvb.datatypes.sensors import Sensors, SensorsEEG, SensorsMEG, SensorsInternal
from tvb.core.adapters.abcadapter import ABCSynchronous
from tvb.core.adapters.exceptions import LaunchException
from tvb.basic.traits.util import read_list_data
from tvb.basic.logger.builder import get_logger


class Sensors_Importer(ABCSynchronous):
    """
    Upload Sensors from a TXT file.
    """ 
    _ui_name = "Sensors"
    _ui_subsection = "sensors_importer"
    _ui_description = "Import Sensor locations from TXT or BZ2"

    EEG_SENSORS = "EEG Sensors"
    MEG_SENSORS = "MEG sensors"
    INTERNAL_SENSORS = "Internal Sensors"
         
    def __init__(self):
        ABCSynchronous.__init__(self)
        self.logger = get_logger(self.__class__.__module__)

    def get_input_tree(self):
        """
        Define input parameters for this importer.
        """
        return [{'name': 'sensors_file', 'type': 'upload', 'required_type':'txt', 
                 'label': 'Please upload sensors file (txt or bz2 format)', 'required': True,
                 'description': 'Expected a text/bz2 file containing sensor measurements.' },
                
                {'name': 'sensors_type', 'type': 'select', 
                 'label': 'Sensors type: ', 'required': True,
                 'options': [{'name':self.EEG_SENSORS,'value': self.EEG_SENSORS},
                             {'name':self.MEG_SENSORS,'value': self.MEG_SENSORS},
                             {'name':self.INTERNAL_SENSORS,'value': self.INTERNAL_SENSORS}]
                 },
                ]
                             
    def get_output(self):
        return [Sensors]

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
    
    def launch(self, sensors_file, sensors_type):
        """
        Created required sensors from the uploaded file.
        """
        if sensors_file is None:
            raise LaunchException ("Please select sensors file which contains data to import")
        sensors_inst = None
        
        self.logger.debug("Create sensors instance")
        if sensors_type == self.EEG_SENSORS:
            sensors_inst = SensorsEEG()
        elif sensors_type == self.MEG_SENSORS:
            sensors_inst = SensorsMEG()
        elif sensors_type == self.INTERNAL_SENSORS:
            sensors_inst = SensorsInternal()
        else:
            exception_str = "Could not determine sensors type (selected option %s)" % sensors_type
            raise LaunchException(exception_str)
            
        sensors_inst.storage_path = self.storage_path
        
        sensors_inst.locations = read_list_data(sensors_file, usecols=[1,2,3])
        sensors_inst.labels = read_list_data(sensors_file, dtype=numpy.str, usecols=[0])
        
        if isinstance(sensors_inst, SensorsMEG):
            try:
                sensors_inst.orientations = read_list_data(sensors_file, usecols=[4,5,6])
            except IndexError:
                raise LaunchException("Uploaded file does not contains sensors orientation.")
         
        self.logger.debug("Sensors instance ready to be stored")
        
        return [sensors_inst]
    
    