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
Created on Jun 29, 2012

.. moduleauthor:: bogdan.neacsa <bogdan.neacsa@codemart.ro>
'''
import os
import tvb_test
import numpy
import unittest
import json
from tvb.config import SIMULATOR_MODULE, SIMULATOR_CLASS
from tvb.basic.config.settings import TVBSettings as cfg
from tvb.core.entities import model
from tvb.core.entities.storage import dao
from tvb.core.entities.file.fileshelper import FilesHelper
from tvb.core.adapters.abcadapter import ABCAdapter
from tvb.adapters.analyzers.metrics_group_timeseries import TimeseriesMetricsAdapter
from tvb.datatypes.time_series import TimeSeriesRegion
from tvb.datatypes.mapped_values import DatatypeMeasure
from tvb.core.entities.transient.structure_entities import DataTypeMetaData
from tvb.core.services.operationservice import OperationService
from tvb.core.services.flowservice import FlowService

from tvb_test.core.test_factory import TestFactory
from tvb_test.core.base_testcase import TransactionalTestCase
from tvb_test.adapters.storeadapter import StoreAdapter


class TimeSeriesMetricsAdapterTest(TransactionalTestCase):
    """
    Test the timeseries metric adapter.
    """
    def setUp(self):
        self.test_user = TestFactory.create_user()
        self.test_project = TestFactory.create_project(self.test_user)
        self.old_config_file = cfg.CURRENT_DIR
        cfg.CURRENT_DIR = os.path.dirname(tvb_test.__file__) 
        TestFactory.import_cff(test_user=self.test_user, test_project=self.test_project)
        
    def tearDown(self):
        """
        Remove project folders and clean up database.
        """
        FilesHelper().remove_project_structure(self.test_project.name)
        cfg.CURRENT_DIR = self.old_config_file
        
    def test_adapter_launch(self):
        """
        Test that the adapters launches and succesfully generates a datatype measure entry.
        """
        meta = {DataTypeMetaData.KEY_SUBJECT : "John Doe", DataTypeMetaData.KEY_STATE : "RAW"}
        _, algo_group = FlowService().get_algorithm_by_module_and_class(SIMULATOR_MODULE, SIMULATOR_CLASS)
        self.operation = model.Operation(self.test_user.id, self.test_project.id, algo_group.id, 
                                         json.dumps(''), 
                                         meta = json.dumps(meta), status="STARTED",
                                         method_name = ABCAdapter.LAUNCH_METHOD)
        self.operation = dao.store_entity(self.operation)
        storage_path = FilesHelper().get_project_folder(self.test_project, str(self.operation.id))
        dummy_input = numpy.arange(1, 10001).reshape(10, 10, 10, 10)
        dummy_time = numpy.arange(1, 11)
        
        # Get connectivity
        connectivities = FlowService().get_available_datatypes(self.test_project.id,
                                                                   "tvb.datatypes.connectivity.Connectivity")
        self.assertEqual(len(connectivities), 1)
        connectivity_gid = connectivities[0][2]
        
        dummy_time_series = TimeSeriesRegion()
        dummy_time_series.storage_path = storage_path
        dummy_time_series.write_data_slice(dummy_input)
        dummy_time_series.write_time_slice(dummy_time)
        dummy_time_series.close_file()
        dummy_time_series.start_time = 0.0
        dummy_time_series.sample_period = 1.0
        dummy_time_series.connectivity = connectivity_gid
        
        
        adapter_instance = StoreAdapter([dummy_time_series])
        OperationService().initiate_prelaunch(self.operation, adapter_instance, {})
        
        dummy_time_series = dao.get_generic_entity(dummy_time_series.__class__, dummy_time_series.gid, 'gid')[0]
        ts_metric_adapter = TimeseriesMetricsAdapter()
        resulted_metric = ts_metric_adapter.launch(dummy_time_series)
        self.assertTrue(isinstance(resulted_metric, DatatypeMeasure), "Result should be a datatype measure.")
        self.assertTrue(len(resulted_metric.metrics) == len(ts_metric_adapter.available_algorithms.keys()),
                        "A result should have been generated for every metric.")
        

def suite():
    """
        Gather all the tests in a test suite.
    """
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(TimeSeriesMetricsAdapterTest))
    return test_suite


if __name__ == "__main__":
    #So you can run tests from this package individually.
    unittest.main()         
        
        
    