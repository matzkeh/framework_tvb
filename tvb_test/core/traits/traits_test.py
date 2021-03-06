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
.. moduleauthor:: Calin Pavel <calin.pavel@codemart.ro>
.. moduleauthor:: Lia Domide <lia.domide@codemart.ro>
"""

import unittest
import numpy
import os
import shutil
import json
from copy import deepcopy
import tvb.datatypes.equations as equations 
import tvb.datatypes.surfaces as surfaces
import tvb.datatypes.arrays as arrays
import tvb.datatypes.time_series as time_series
from tvb.datatypes.equations import Equation
from tvb.basic.traits.types_basic import MapAsJson
from tvb.basic.traits.types_mapped import MappedType
from tvb.basic.traits import types_basic as basic
from tvb.basic.config.settings import TVBSettings as config
from tvb.simulator.models import WilsonCowan, ReducedSetHindmarshRose
from tvb_library_test.base_testcase import BaseTestCase


class MappedTypeStorageTests(unittest.TestCase):
    """
    Test class for testing mapped type data storage into file.
    Most of the storage functionality is tested in the test suite 
    of HDF5StorageManager 
    """
    def setUp(self):
        """
        Prepare data for tests
        """
        storage_folder = os.path.join(config.TVB_STORAGE, "test_hdf5")

        if os.path.exists(storage_folder):
            shutil.rmtree(storage_folder)
        os.makedirs(storage_folder)
        
        # Create data type for which to store data
        self.data_type = MappedType()
        self.data_type.storage_path = storage_folder
        
        self.test_2D_array = numpy.random.random((10, 10))
        self.data_name = "vertex"

    def tearDown(self):
        """
        Clean up tests data
        """
        if os.path.exists(self.data_type.storage_path):
            shutil.rmtree(self.data_type.storage_path)
    
    def test_store_data(self):
        """
        Test data storage into file
        """
        self.data_type.store_data(self.data_name, self.test_2D_array)
        read_data = self.data_type.get_data(self.data_name)
        numpy.testing.assert_array_equal(self.test_2D_array, read_data, "Did not get the expected data")
    
    def test_store_chunked_data(self):
        """
        Test data storage into file, but splitted in chunks
        """
        self.data_type.store_data_chunk(self.data_name, self.test_2D_array)
        read_data = self.data_type.get_data(self.data_name)
        numpy.testing.assert_array_equal(self.test_2D_array, read_data, "Did not get the expected data")
    
    
    def test_set_metadata(self):
        """
        This test checks assignment of metadata to dataset or storage file  
        """
        # First create some data and check if it is stored
        self.data_type.store_data(self.data_name, self.test_2D_array)
        
        key = "meta_key"
        value = "meva_val"
        self.data_type.set_metadata({key:value}, self.data_name)
        read_meta_data = self.data_type.get_metadata(self.data_name)
        self.assertEqual(value, read_meta_data[key], "Meta value is not correct")
        
        # Now we'll store metadata on file /root node
        self.data_type.set_metadata({key:value})
        read_meta_data = self.data_type.get_metadata()
        self.assertEqual(value, read_meta_data[key], "Meta value is not correct")
        
    def test_remove_metadata(self):
        """
        This test checks removal of metadata from dataset 
        """
        # First create some data and check if it is stored
        self.data_type.store_data(self.data_name, self.test_2D_array)
        
        key = "meta_key"
        value = "meva_val"
        self.data_type.set_metadata({key:value}, self.data_name)
        read_meta_data = self.data_type.get_metadata(self.data_name)
        self.assertEqual(value, read_meta_data[key], "Meta value is not correct")
        
        # Now delete metadata
        self.data_type.remove_metadata(key, self.data_name)
        read_meta_data = self.data_type.get_metadata(self.data_name)
        self.assertEqual(0, len(read_meta_data), "There should be no metadata on node")
        
        
def suite():
    """
    Gather all the tests in a test suite.
    """
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(MappedTypeStorageTests))
    return test_suite


if __name__ == "__main__":
    #So you can run tests from this package individually.
    TEST_RUNNER = unittest.TextTestRunner()
    TEST_SUITE = suite()
    TEST_RUNNER.run(TEST_SUITE) 
    
    
    
    