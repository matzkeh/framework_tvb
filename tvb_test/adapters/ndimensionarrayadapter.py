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
.. moduleauthor:: Bogdan Neacsa <bogdan.neacsa@codemart.ro>
.. moduleauthor:: Lia Domide <lia.domide@codemart.ro>
"""

import numpy
from tvb.datatypes.arrays import MappedArray
from tvb.core.adapters.abcadapter import ABCSynchronous



class NDimensionArrayAdapter(ABCSynchronous):
    """
    Adapter for creating a persisted array.
    """
    
    def __init__(self):
        super(NDimensionArrayAdapter, self).__init__()
        self.launch_param = None

    def get_input_tree(self):
        """
        Returns the interface which should contain a component which allows
        the user to select one dimension from a multi dimensins array.
        """
        return [{'name': 'input_data', 'label': 'Array 1: ', 'required': True, 'type': MappedArray, 'datatype': True,
                 'description': '-', 'ui_method': 'reduceDimension', 'python_method': 'reduce_dimension', 
                 'parameters_prefix': 'dimensions', 'parameters': {'required_dimension': '1'} } ]
        
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

    def get_output(self):
        return [MappedArray]


    def launch(self, input_data=None):
        """
        Saves in the db the following array.
        """
        self.launch_param = input_data
        array_inst = MappedArray()
        array_inst.storage_path = self.storage_path
        array_inst.array_data = numpy.array(range(1, 46)).reshape((5, 3, 3))
        array_inst.type = "MappedArray"
        array_inst.module = "tvb.datatypes.arrays"
        array_inst.subject = "John Doe"
        array_inst.state = "RAW"
        return array_inst


    
    
    
    
    