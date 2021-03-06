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
Used by FlowController.
It will store in current user's session information about 

.. moduleauthor:: Lia Domide <lia.domide@codemart.ro>
"""

import tvb.interfaces.web.controllers.basecontroller as base


class SelectedAdapterContext(object):
    """
    Responsible for storing/retrieving/removing from session info about currently selected algorithm.
    """
    
    KEY_CURRENT_ADAPTER_INFO = "currentAdapterInfo"
    _KEY_INPUT_TREE = "inputList"
    _KEY_CURRENT_STEP = "currentStepCategoryId"
    _KEY_CURRENT_SUBSTEP = "currentAlgoGroupId"
    _KEY_SELECTED_DATA = 'defaultData'
    KEY_PORTLET_CONFIGURATION = 'portletConfig'
    KEY_TREE_DEFAULT = "defaultTree"

    def add_adapter_to_session(self, algo_group, input_tree, default_data=None):
        """
        Put in session information about currently selected adapter.
        Will be used by filters and efficiency load.
        """
        previous_algo = self.get_current_substep()  
        current_algo = algo_group.id if algo_group is not None else (default_data[base.KEY_ADAPTER] 
                                                                     if default_data is not None else None)
        if current_algo is None or str(current_algo) != str(previous_algo):
            self.clean_from_session()
            adapter_info = {}
        else:
            adapter_info = base.get_from_session(self.KEY_CURRENT_ADAPTER_INFO)
            
        if default_data is not None: 
            adapter_info[self._KEY_SELECTED_DATA] = default_data
        if input_tree is not None:
            adapter_info[self._KEY_INPUT_TREE] = input_tree
        if algo_group is not None:
            adapter_info[self._KEY_CURRENT_STEP] = algo_group.fk_category 
            adapter_info[self._KEY_CURRENT_SUBSTEP] = algo_group.id 
                
        base.add2session(self.KEY_CURRENT_ADAPTER_INFO, adapter_info)
     
     
    def add_portlet_to_session(self, portlet_interface):
        """
        Add a portlet configuration to the session. Used for applying filters on
        portlet configurations.
        """
        full_description = base.get_from_session(self.KEY_CURRENT_ADAPTER_INFO)
        if full_description is None or full_description is {}:
            raise Exception("Should not add portlet interface to session")
        full_description[self.KEY_PORTLET_CONFIGURATION] = portlet_interface
    
    
    def get_current_input_tree(self):
        """
        Get from session previously selected InputTree.
        """
        full_description = base.get_from_session(self.KEY_CURRENT_ADAPTER_INFO)
        if full_description is not None and self._KEY_INPUT_TREE in full_description:
            return full_description[self._KEY_INPUT_TREE]
        return None
    
    def get_session_tree_for_key(self, tree_session_key):
        """
        Get from session previously selected InputTree stored under the @param tree_session_key.
        """
        if tree_session_key == self.KEY_TREE_DEFAULT:
            return self.get_current_input_tree()
        full_description = base.get_from_session(self.KEY_CURRENT_ADAPTER_INFO)
        if full_description is not None and tree_session_key in full_description:
            return full_description[tree_session_key]
        return None
    
    
    def get_current_step(self):
        """
        Get from session previously selected step (category ID).
        """
        full_description = base.get_from_session(self.KEY_CURRENT_ADAPTER_INFO)
        if full_description is not None and self._KEY_CURRENT_STEP in full_description:
            return full_description[self._KEY_CURRENT_STEP]
        return None
    
    def get_current_substep(self):
        """
        Get from session previously selected step (algo-group ID).
        """
        full_description = base.get_from_session(self.KEY_CURRENT_ADAPTER_INFO)
        if full_description is not None and self._KEY_CURRENT_SUBSTEP in full_description:
            return full_description[self._KEY_CURRENT_SUBSTEP]
        selected_data_step = self.get_current_default(base.KEY_ADAPTER)
        if full_description is not None and selected_data_step is not None:
            return selected_data_step
        return None
    
    def get_current_default(self, param_name=None):
        """
        Read from session previously stored default data.
        :param param_name: When None, return full dictionary with defaults.
        """
        full_description = base.get_from_session(self.KEY_CURRENT_ADAPTER_INFO)
        if full_description is None or self._KEY_SELECTED_DATA not in full_description:
            return None
        full_default = full_description[self._KEY_SELECTED_DATA]
        if param_name is None:
            return full_default
        if full_default is not None and param_name in full_default:
            return full_default[param_name]
        return None
    
    def clean_from_session(self):
        """
        Remove info about selected algo from session
        """
        base.remove_from_session(self.KEY_CURRENT_ADAPTER_INFO)
        


