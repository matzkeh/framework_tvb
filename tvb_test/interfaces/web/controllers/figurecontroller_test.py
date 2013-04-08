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
import unittest
import cherrypy
from tvb.interfaces.web.controllers.project.figurecontroller import FigureController
from tvb.core.entities.storage import dao
from tvb_test.core.base_testcase import TransactionalTestCase
from tvb_test.interfaces.web.controllers.basecontroller_test import BaseControllersTest
from tvb_test.core.test_factory import TestFactory


class FigureControllerTest(TransactionalTestCase, BaseControllersTest):
    """ Unit tests for helpcontroller """
    
    def setUp(self):
        BaseControllersTest.init(self)
        self.figure_c = FigureController()
        self.operation = TestFactory.create_operation(test_user = self.test_user, 
                                                      test_project = self.test_project)
    
    
    def tearDown(self):
        BaseControllersTest.cleanup(self)
            
            
    def test_displayresultfigures(self):
        figure1 = TestFactory.create_figure(self.operation.id, self.test_user.id, 
                                            self.test_project.id, name="figure1", 
                                            path="path-to-figure1", session_name="test")
        figure2 = TestFactory.create_figure(self.operation.id, self.test_user.id, 
                                            self.test_project.id, name="figure2", 
                                            path="path-to-figure2", session_name="test")
        result_dict = self.figure_c.displayresultfigures()
        figures = result_dict['selected_sessions_data']['test']
        self.assertEqual(set([fig.id for fig in figures]), set([figure1.id, figure2.id]))
        
        
    def test_editresultfigures_remove_fig(self):
        cherrypy.request.method = 'POST'
        figure1 = TestFactory.create_figure(self.operation.id, self.test_user.id, 
                                            self.test_project.id, name="figure1", 
                                            path="path-to-figure1", session_name="test")
        figs = dao.get_figures_for_operation(self.operation.id)
        self.assertEqual(len(figs), 1)
        data = {'figure_id' : figure1.id}
        self._expect_redirect('/project/figure/displayresultfigures', self.figure_c.editresultfigures,
                              remove_figure=True, **data)
        figs = dao.get_figures_for_operation(self.operation.id)
        self.assertEqual(len(figs), 0)
        
        
    def test_editresultfigures_rename_session(self):
        cherrypy.request.method = 'POST'
        TestFactory.create_figure(self.operation.id, self.test_user.id, 
                                            self.test_project.id, name="figure1", 
                                            path="path-to-figure1", session_name="test")
        TestFactory.create_figure(self.operation.id, self.test_user.id, 
                                            self.test_project.id, name="figure2", 
                                            path="path-to-figure2", session_name="test")
        figs, _ = dao.get_previews(self.test_project.id, self.test_user.id, "test")  
        self.assertEqual(len(figs['test']), 2)
        data = {'old_session_name' : 'test', 'new_session_name' : 'test_renamed'}
        self._expect_redirect('/project/figure/displayresultfigures', self.figure_c.editresultfigures,
                              rename_session=True, **data)
        figs, previews = dao.get_previews(self.test_project.id, self.test_user.id, "test")
        self.assertEqual(len(figs['test']), 0)
        self.assertEqual(previews['test_renamed'], 2)
            
            
    def test_editresultfigures_remove_session(self):
        cherrypy.request.method = 'POST'
        TestFactory.create_figure(self.operation.id, self.test_user.id, 
                                            self.test_project.id, name="figure1", 
                                            path="path-to-figure1", session_name="test")
        TestFactory.create_figure(self.operation.id, self.test_user.id, 
                                            self.test_project.id, name="figure2", 
                                            path="path-to-figure2", session_name="test")
        figs, _ = dao.get_previews(self.test_project.id, self.test_user.id, "test")  
        self.assertEqual(len(figs['test']), 2)
        data = {'old_session_name' : 'test', 'new_session_name' : 'test_renamed'}
        self._expect_redirect('/project/figure/displayresultfigures', self.figure_c.editresultfigures,
                              remove_session=True, **data)
        figs, previews = dao.get_previews(self.test_project.id, self.test_user.id, "test")
        self.assertEqual(len(figs['test']), 0)
        self.assertEqual(previews, {})
            
            
def suite():
    """
    Gather all the tests in a test suite.
    """
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(FigureControllerTest))
    return test_suite


if __name__ == "__main__":
    #So you can run tests individually.
    TEST_RUNNER = unittest.TextTestRunner()
    TEST_SUITE = suite()
    TEST_RUNNER.run(TEST_SUITE)