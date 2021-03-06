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
import os
import unittest
import demoData.surfaceData as surface_dataset
import demoData.sensors as sensors_dataset
from tvb.core.entities.file.fileshelper import FilesHelper
from tvb_test.datatypes.datatypes_factory import DatatypesFactory
from tvb_test.core.base_testcase import TransactionalTestCase
from tvb.core.services.flowservice import FlowService
from tvb.core.adapters.abcadapter import ABCAdapter
from tvb.datatypes.surfaces import CorticalSurface, FaceSurface, EEGCap
from tvb.datatypes.connectivity import Connectivity
from tvb.datatypes.sensors import SensorsEEG
from tvb.adapters.visualizers.brain import BrainViewer, BrainEEG
from tvb_test.core.test_factory import TestFactory


class BrainViewerTest(TransactionalTestCase):
    """
    Unit-tests for BrainViewer.
    """
    def setUp(self):
        self.datatypeFactory = DatatypesFactory()
        self.test_project = self.datatypeFactory.get_project()
        self.test_user = self.datatypeFactory.get_user()
        
        TestFactory.import_cff(test_user = self.test_user, test_project=self.test_project)
        zip_path = os.path.join(os.path.dirname(surface_dataset.__file__), 'face-surface.zip')
        TestFactory.import_surface_zip(self.test_user, self.test_project, zip_path, 'Face', 1)
        zip_path = os.path.join(os.path.dirname(surface_dataset.__file__), 'eeg_skin_surface.zip')
        TestFactory.import_surface_zip(self.test_user, self.test_project, zip_path, 'EEG Cap', 1)
        self.connectivity = self._get_entity(Connectivity())
        self.assertTrue(self.connectivity is not None)
        self.surface = self._get_entity(CorticalSurface())
        self.assertTrue(self.surface is not None)
        self.face_surface = self._get_entity(FaceSurface())
        self.assertTrue(self.face_surface is not None)
        self.assertTrue(self._get_entity(EEGCap()) is not None)
                
    def tearDown(self):
        """
        Clean-up tests data
        """
        FilesHelper().remove_project_structure(self.test_project.name)
    
    def _get_entity(self, expected_data, filters = None):
        data_types = FlowService().get_available_datatypes(self.test_project.id,
                                expected_data.module + "." + expected_data.type, filters)
        self.assertEqual(1, len(data_types), "Project should contain only one data type:" + str(expected_data.type))
        entity = ABCAdapter.load_entity_by_gid(data_types[0][2])
        self.assertTrue(entity is not None, "Instance should not be none")
        return entity
    
    
    def test_launch(self):
        """
        Check that all required keys are present in output from BrainViewer launch.
        """
        time_series = self.datatypeFactory.create_timeseries(self.connectivity)
        viewer = BrainViewer()
        result = viewer.launch(time_series=time_series)
        expected_keys = ['urlVertices', 'urlNormals', 'urlTriangles', 'urlMeasurePointsLabels', 'title', 
                         'time_series', 'shelfObject', 'pageSize', 'nrOfStateVar', 'nrOfPages', 'nrOfModes',
                         'minActivityLabels', 'minActivity', 'measure_points', 'maxActivity', 'isOneToOneMapping',
                         'isAdapter', 'extended_view', 'base_activity_url', 'alphas_indices']
        for key in expected_keys:
            self.assertTrue(key in result and result[key] is not None)
        self.assertFalse(result['extended_view'])

    
    def test_get_required_memory(self):
        """
        Brainviewer should know required memory so expect positive number and not -1.
        """
        time_series = self.datatypeFactory.create_timeseries(self.connectivity)
        self.assertTrue(BrainViewer().get_required_memory_size(time_series) > 0)
        
        
    def test_generate_preview(self):
        """
        Check that all required keys are present in preview generate by BrainViewer.
        """
        time_series = self.datatypeFactory.create_timeseries(self.connectivity)
        viewer = BrainViewer()
        result = viewer.generate_preview(time_series, (500, 200))
        expected_keys = ['urlVertices', 'urlNormals', 'urlTriangles', 'pageSize', 'nrOfPages', 
                         'minActivityLabels', 'minActivity', 'maxActivity', 'isOneToOneMapping',
                         'isAdapter', 'base_activity_url', 'alphas_indices']
        for key in expected_keys:
            self.assertTrue(key in result and result[key] is not None)
        
        
#    def test_launch_eeg(self):
#        zip_path = os.path.join(os.path.dirname(sensors_dataset.__file__), 'EEG_unit_vectors_BrainProducts_62.txt.bz2')
#        
#        TestFactory.import_sensors(self.test_user, self.test_project, zip_path, 'EEG Sensors')
#        sensors = self._get_entity(SensorsEEG())
#        time_series = self.datatypeFactory.create_timeseries(self.connectivity, 'EEG', sensors)
#        time_series.configure()
#        viewer = BrainEEG()
#        result = viewer.launch(time_series)
#        expected_keys = ['urlVertices', 'urlNormals', 'urlTriangles', 'urlMeasurePointsLabels', 'title', 
#                         'time_series', 'shelfObject', 'pageSize', 'nrOfStateVar', 'nrOfPages', 'nrOfModes',
#                         'minActivityLabels', 'minActivity', 'measure_points', 'maxActivity', 'isOneToOneMapping',
#                         'isAdapter', 'extended_view', 'base_activity_url', 'alphas_indices']
#        for key in expected_keys:
#            self.assertTrue(key in result and result[key] is not None)
#        self.assertTrue(result['extended_view'])
    
        
def suite():
    """
    Gather all the tests in a test suite.
    """
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(BrainViewerTest))
    return test_suite


if __name__ == "__main__":
    #So you can run tests from this package individually.
    TEST_RUNNER = unittest.TextTestRunner()
    TEST_SUITE = suite()
    TEST_RUNNER.run(TEST_SUITE)