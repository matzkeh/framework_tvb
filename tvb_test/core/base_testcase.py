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
"""

import unittest
import os
import cherrypy
import shutil
from types import FunctionType
from tvb.basic.config.utils import EnhancedDictionary
from tvb.basic.config.settings import TVBSettings as cfg
from tvb.basic.logger.builder import get_logger
from tvb.core.utils import get_matlab_executable
from tvb.core.entities.storage import dao
from tvb.core.entities.storage.sessionmaker import SessionMaker
from tvb.core.entities import model
from tvb.core.entities.modelmanager import reset_database
from tvb.core.services.initializer import initialize
from tvb.core.services.operationservice import OperationService

LOGGER = get_logger(__name__)
MATLAB_EXECUTABLE = get_matlab_executable()

def init_test_env():
    """
        This method prepares all necessary data for tests execution
    """
    default_mlab_exe = cfg.MATLAB_EXECUTABLE
    cfg.MATLAB_EXECUTABLE = get_matlab_executable()
    reset_database()
    initialize(["tvb.config", "tvb_test"], load_xml_events = False)
    cfg.MATLAB_EXECUTABLE = default_mlab_exe
    
    
def transactional_test(func, callback=None):
    """
    A decorator to be used in tests which makes sure all database changes are reverted
    at the end of the test.
    """
    if func.__name__.startswith('test_'):
        def dec(*args, **kwargs):
            session_maker = SessionMaker()
            cfg.ALLOW_NESTED_TRANSACTIONS = True
            default_dir = cfg.CURRENT_DIR
            default_mlab_exe = cfg.MATLAB_EXECUTABLE
            cfg.MATLAB_EXECUTABLE = get_matlab_executable()
            session_maker.start_transaction()
            try:
                try:
                    if hasattr(args[0], 'setUpTVB'):
                        args[0].setUpTVB()
                    result = func(*args, **kwargs)
                finally:
                    if hasattr(args[0], 'tearDownTVB'):
                        args[0].tearDownTVB()
                        args[0].delete_project_folders()
            finally:
                session_maker.rollback_transaction()
                session_maker.close_transaction()
                cfg.ALLOW_NESTED_TRANSACTIONS = False
                cfg.MATLAB_EXECUTABLE = default_mlab_exe
                cfg.CURRENT_DIR = default_dir
            if callback is not None:
                callback(*args, **kwargs)
            return result
        return dec
    else:
        return func

class TransactionalTestMeta(type):
    """
    New MetaClass.
    """
    def __new__(mcs, classname, bases, class_dict):
        """
        Called when a new class gets instantiated.
        """
        new_class_dict = {}
        for attr_name, attribute in class_dict.items():
            if (type(attribute) == FunctionType and not (attribute.__name__.startswith('__') 
                                                         and attribute.__name__.endswith('__'))):
                if attr_name.startswith('test_'):
                    attribute = transactional_test(attribute)
                if attr_name in ('setUp', 'tearDown'):
                    new_class_dict[attr_name + 'TVB'] = attribute
                else:
                    new_class_dict[attr_name] = attribute
            else:
                new_class_dict[attr_name] = attribute
        return  type.__new__(mcs, classname, bases, new_class_dict)

# Following code is executed once / tests execution to reduce time.
if "TEST_INITIALIZATION_DONE" not in globals():
    init_test_env()
    TEST_INITIALIZATION_DONE = True
    
    
class BaseTestCase(unittest.TestCase):
    """
        This class should implement basic functionality which 
        is common to all TVB tests.
    """
    EXCLUDE_TABLES = ["ALGORITHMS", "ALGORITHM_GROUPS", "ALGORITHM_CATEGORIES", "PORTLETS", 
                      "MAPPED_INTERNAL__CLASS", "MAPPED_MAPPED_TEST_CLASS"]
    
    def assertEqual(self, expected, actual, message=""):
        super(BaseTestCase, self).assertEqual(expected, actual, message + " Expected %s but got %s."%(expected, actual))
    
    def clean_database(self, delete_folders=True):
        """
            Deletes data from all tables
        """
        self.cancel_all_operations()
        LOGGER.warning("Your Database content will be deleted.")
        try:
            session = SessionMaker()
            for table in reversed(model.Base.metadata.sorted_tables):
                # We don't delete data from some tables, because those are 
                # imported only during introspection which is done one time
                if table.name not in self.EXCLUDE_TABLES:
                    try:
                        session.open_session()
                        con = session.connection()
                        LOGGER.debug("Executing Delete From Table " + table.name)
                        con.execute(table.delete())
                        session.commit()
                    except Exception, e:
                        # We cache exception here, in case some table does not exists and
                        # to allow the others to be deleted
                        LOGGER.warning(e)
                        session.rollback()
                    finally:
                        session.close_session()
            LOGGER.info("Database was cleanup!")
        except Exception, excep:
            LOGGER.warning(excep)
            raise
        
        # Now if the database is clean we can delete also project folders on disk
        if delete_folders:
            self.delete_project_folders()
        dao.store_entity(model.User(cfg.SYSTEM_USER_NAME, 
                                    None, None, True, None))
        
    def cancel_all_operations(self):
        """
        To make sure that no running operations are left which could make some other
        test started afterwards to fail, cancel all operations after each test.
        """
        LOGGER.info("Stopping all operations.")
        op_service = OperationService()
        operations = self.get_all_entities(model.Operation)
        for operation in operations:
            op_service.stop_operation(operation.id)
        
    
    def delete_project_folders(self):
        """
            This method deletes folders for all projects from TVB folder.
            This is done without any check on database. You might get 
            projects in DB but no folder for them on disk.
        """
        if os.path.exists(cfg.TVB_STORAGE):
            for current_file in os.listdir(cfg.TVB_STORAGE):
                full_path = os.path.join(cfg.TVB_STORAGE, current_file) 
                if (current_file != "db_repo" and os.path.isdir(full_path)):
                    shutil.rmtree(full_path, ignore_errors=True)
    
                
    def get_all_entities(self, entity_type):
        """
        Retrieve all entities of a given type."""
        result = []
        try:
            session = SessionMaker()
            session.open_session()
            result = session.query(entity_type).all()
        except Exception, excep:
            LOGGER.warning(excep)
        finally:
            session.close_session()
        return result
    
    
    def get_all_datatypes(self):
        """Return all DataType entities in DB or []."""
        return self.get_all_entities(model.DataType)
    
        
    def reset_database(self):
        init_test_env()
        
class TransactionalTestCase(BaseTestCase):
    """
    This class makes sure that any test case it contains is ran in a transactional
    environment and a rollback is issued at the end of that transaction. This should
    imporve performance for most cases. 
    
    WARNING! Do not use this is any test class that has uses multiple threads to do
    dao related operations since that might cause errors/leave some dangling sessions.
    """
    __metaclass__ = TransactionalTestMeta
        
