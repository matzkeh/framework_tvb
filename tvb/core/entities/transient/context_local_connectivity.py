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
Created on Aug 23, 2012

.. moduleauthor:: bogdan.neacsa <bogdan.neacsa@codemart.ro>
'''

class ContextLocalConnectivity():
    """
    Keep the required data to redo the whole page. We don't need to keep the kwargs since
    we never return to that page in 'create mode', so the local connectivity entity and the
    selected surface should suffice.
    """    
    def __init__(self):
        self.selected_entity = None
        self.selected_surface = None
    
    def reset(self):
        self.selected_entity = None
        self.selected_surface = None