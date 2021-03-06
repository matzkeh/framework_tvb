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
Created on Jul 21, 2011

.. moduleauthor:: Ionel Ortelecan <ionel.ortelecan@codemart.ro>
.. moduleauthor:: Bogdan Neacsa <bogdan.neacsa@codemart.ro>
'''

import os
import unittest
from tvb.core.entities.storage import dao
from tvb.core.adapters.introspector import Introspector
from tvb.core.services.projectservice import initialize_storage
from tvb.basic.config.settings import TVBSettings as cfg
from tvb_test.core.base_testcase import BaseTestCase

class IntrospectorTest(BaseTestCase):
    """
    Test class for the introspector module.
    """
    
    def setUp(self):
        """
        Reset the database before each test.
        """
        self.reset_database()
        #tvb_test path
        core_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.old_path = cfg.CURRENT_DIR
        cfg.CURRENT_DIR = os.path.dirname(core_path)
        self.introspector = Introspector("tvb_test")
        
        
    def tearDown(self):
        """
        Reset the database when test is done.
        """
        cfg.CURRENT_DIR = self.old_path
        self.reset_database()
        
    def test_introspect(self):
        """
        Test the actual introspect module on a test structure created in:
        tvb_test.dummy_adapters and tvb_test.dummy_datatypes
        """ 
        self.introspector.introspect(True)
        initialize_storage()
        
        all_categories = dao.get_algorithm_categories()
        category_ids = [cat.id for cat in all_categories if cat.displayname == "AdaptersTest"]
        groups = dao.get_groups_by_categories(category_ids)
        self.assertEqual(len(groups), 11, "Introspection failed!")
        nr_adapters_mod2 = 0
        for algorithm in groups:
            self.assertTrue(algorithm.module in ['tvb_test.adapters.testadapter1', 'tvb_test.adapters.testadapter2',
                                                 'tvb_test.adapters.testadapter3',
                                                 'tvb_test.adapters.ndimensionarrayadapter', 
                                                 "tvb.adapters.analyzers.group_python_adapter",
                                                 "tvb_test.adapters.testgroupadapter"],
                            "Unknown Adapter:" + str(algorithm.module))
            self.assertTrue(algorithm.classname in ["TestAdapter1", "TestAdapterDatatypeInput",  
                                                    "TestAdapter2", "TestAdapter22", "TestAdapter3", 
                                                    "NDimensionArrayAdapter", "PythonAdapter",  "TestAdapterHDDRequired",
                                                    "TestAdapterHugeMemoryRequired", "TestAdapterNoMemoryImplemented", "TestGroupAdapter"],
                            "Unknown Adapter Class:" + str(algorithm.classname))
            if algorithm.module == 'tvb_test.adapters.testadapter2':
                nr_adapters_mod2 = nr_adapters_mod2 + 1
        self.assertEqual(nr_adapters_mod2, 2, "Two adapters should have been loaded from module tvb_test.adapters2!")


    def test_xml_introspection(self):
        """
        Check the XML introspection. The folders which are introspected
        are defined in the variable __xml_folders__ from tvb_test/adapters/_init.py
        """
        self.introspector.introspect(True)
        initialize_storage()
        init_parameter = os.path.join("core", "adapters", "test_group.xml")
        group = dao.find_group("tvb_test.adapters.testgroupadapter", "TestGroupAdapter", init_parameter)
        self.assertTrue(group is not None, "The group was not found")
        self.assertEqual(group.init_parameter, init_parameter, "Wrong init_parameter:" + str(group.init_parameter))
        self.assertEqual(group.displayname, "Simple Python Analyzers", "The display-name of the group is not valid")
        self.assertEqual(group.algorithm_param_name, "simple", "The algorithm_param_name of the group is not valid")
        self.assertEqual(group.classname, "TestGroupAdapter", "The class-name of the group is not valid")
        self.assertEqual(group.module, "tvb_test.adapters.testgroupadapter", "Group Module invalid")

        
def suite():
    """
    Gather all the tests in a test suite.
    """
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(IntrospectorTest))
    return test_suite


if __name__ == "__main__":
    #To run tests individually.
    unittest.main()  
    
