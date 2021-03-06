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
"""

import datetime
from tvb.core.utils import date2string

class Exportable(object):
    
    def to_dict(self, excludes=['id']):
        """
        For a model entity, return a equivalent dictionary.
        """
        dict_equivalent = {}
        for key in self.__dict__:
            if '_sa_' not in key[:5] and key not in excludes:
                if isinstance(self.__dict__[key], datetime.datetime):
                    dict_equivalent[key] = date2string(self.__dict__[key])
                else:
                    dict_equivalent[key] = self.__dict__[key]
        return self.__class__.__name__, dict_equivalent
        
    def from_dict(self, dictionary):
        pass