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
A mapping from traited datatypes to sql types.

.. moduleauthor:: Bogdan Neacsa <bogdan.neacsa@codemart.ro>
"""
import sqlalchemy

MAPPINGS = {
            'tvb.basic.traits.types_basic.String' : (sqlalchemy.String, ),
            'tvb.basic.traits.types_basic.Bool' : (sqlalchemy.Boolean, ),
            'tvb.basic.traits.types_basic.Integer' : (sqlalchemy.Integer, ),
            'tvb.basic.traits.types_basic.Float' : (sqlalchemy.Float, ),
            'tvb.basic.traits.types_basic.Complex' : None,
            'tvb.basic.traits.types_basic.MapAsJson' : (sqlalchemy.String, ),
            'tvb.basic.traits.types_mapped_light.Array' : (sqlalchemy.String, )
            }

def get_sql_mapping(input_class):
    """
    Look for a SQL-alchemy mapping for the parameter input_class. 
    Also go through all its base classes and check if any of them have a mapping.
    """
    class_dict_key = input_class.__module__ + '.' + input_class.__name__
    if class_dict_key in MAPPINGS:
        return MAPPINGS[class_dict_key]
    for base_c in input_class.__bases__:
        mapping = get_sql_mapping(base_c)
        if mapping is not False:
            return mapping
    return False

