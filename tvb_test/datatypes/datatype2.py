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
.. moduleauthor:: Bogdan Neacsa <bogdan.neacsa@codemart.ro>
'''
import numpy
from tvb.basic.traits.types_basic import String
from tvb.basic.traits.types_mapped import MappedType
from tvb.datatypes.arrays import StringArray


class Datatype2(MappedType):
    """
        This class is used for testing purposes only.
    """
    row1 = String(label = "spatial_parameters", default="test-spatial")
    row2 = String(label = "temporal_parameters", default="test-temporal")
    
    string_data = StringArray(label = "String data")
    
    def return_test_data(self, length=0):
        return numpy.arange(length)
    
    