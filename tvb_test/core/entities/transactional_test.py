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
import threading
from tvb.config import EVENTS_FOLDER
from tvb.basic.config.settings import TVBSettings as cfg
from tvb.core.entities import model
from tvb.core.entities.storage import dao, transactional
from tvb.core.entities.storage.sessionmaker import add_session, SessionMaker
from tvb.core.entities.storage.exceptions import NestedTransactionUnsupported
from tvb_test.core.test_factory import TestFactory
from tvb_test.core.base_testcase import BaseTestCase, transactional_test

SESSIONMAKER = SessionMaker()

class TransactionalTests(BaseTestCase):
    """
    This class contains tests for the tvb.core.entities.modelmanager module.
    """
    session = SessionMaker()
    
    def setUp(self):
        self.clean_database()
        self.old_events = EVENTS_FOLDER
        
    def tearDown(self):
        self.clean_database(True)
        EVENTS_FOLDER = self.old_events
    

    def test_transaction_happy_flow(self):
        """
        In case no exception is raised the transactional decorator should not influence the data in any way.
        A successfull commit will be made and the data should be visible in the database.
        """
        all_users = dao.get_all_users()
        initial_user_count = len(all_users) if all_users is not None else 0
        n_of_users = 21
        self._store_users_happy_flow(n_of_users)
        final_user_count = dao.get_all_users(is_count=True)
        error_msg = ("Transaction should have committed and %s more users "
                    "should have been available in the database. Expected %s but got %s"%(n_of_users, 
                                                        initial_user_count + n_of_users, final_user_count))
        self.assertEqual(initial_user_count + n_of_users, final_user_count, error_msg)
    
    
    def test_transaction_rollback(self):
        """
        If an unhandled exception is raised by a method marked as transactional, all data should be rolled
        back properly.
        """
        all_users = dao.get_all_users()
        initial_user_count = len(all_users) if all_users is not None else 0
        n_of_users = 6
        try:
            self._store_users_raises_exception(n_of_users)
        except Exception:
            pass
        final_user_count = dao.get_all_users(is_count=True)
        self.assertEqual(initial_user_count, final_user_count, "Transaction should have rolled back due to exception."
                         "Expected %s but got %s"%(initial_user_count, final_user_count))
        
        
    def test_add_entity_forget_commit(self):
        """
        Commit should be done automatically if you forget for some reason to do so in case of new/update/deletes.
        """
        all_users = dao.get_all_users()
        initial_user_count = len(all_users) if all_users is not None else 0
        self._dao_add_user_forget_commit()
        final_user_count = dao.get_all_users(is_count=True)
        self.assertEqual(initial_user_count + 1, final_user_count, "Commit should have been done automatically and one more user expected."
                         "Expected %s but got %s"%(initial_user_count, final_user_count))
        
        
    def test_edit_entity_forget_commit(self):
        """
        Commit should be done automatically if you forget for some reason to do so in case of new/update/deletes.
        """
        stored_user = TestFactory.create_user('username', 'password', 'mail', True, 'role')
        user_id = stored_user.id
        self._dao_change_user_forget_commit(user_id, 'new_name')
        edited_user = dao.get_user_by_id(user_id)
        self.assertEqual(edited_user.username, 'new_name', "User should be edited but isnt. Expected 'new_name' got %s"%(edited_user.username,))
        
        
    def test_delete_entity_forget_commit(self):
        """
        Commit should be done automatically if you forget for some reason to do so in case of new/update/deletes.
        """
        all_users = dao.get_all_users()
        initial_user_count = len(all_users) if all_users is not None else 0
        stored_user = TestFactory.create_user('username', 'password', 'mail', True, 'role')
        user_id = stored_user.id
        self._dao_delete_user_forget_commit(user_id)
        final_user_count = dao.get_all_users(is_count=True)
        self.assertEqual(initial_user_count, final_user_count, "Added user should have been deleted even without explicti commit call.."
                         "Expected %s but got %s"%(initial_user_count, final_user_count))

    
    def test_multi_threaded_access(self):
        """
        Test that there is no problem with multiple threads accessing dao. Since cfg.MAX_THREADS_NO is set to 20 we just
        spawn 4 threads each storing 4 users.
        """
        all_users = dao.get_all_users()
        initial_user_count = len(all_users) if all_users is not None else 0
        n_of_threads = 4
        n_of_users_per_thread = 4
        self._run_transaction_multiple_threads(n_of_threads, n_of_users_per_thread)
        final_user_count = dao.get_all_users(is_count=True)
        self.assertEqual(initial_user_count + n_of_threads * n_of_users_per_thread, final_user_count, 
                         "Each thread should have created %s more users to a total of 16."
                         "Expected %s but got %s"%(n_of_threads * n_of_users_per_thread, 
                                                   initial_user_count + n_of_threads * n_of_users_per_thread, final_user_count))
        
            
    def test_multi_threaded_access_overflow_db_connection(self):
        """
        Test that there is no problem with multiple threads accessing dao. Since cfg.MAX_THREADS_NO is set to 20 we just
        spawn 4 threads each storing 4 users.
        """
        all_users = dao.get_all_users()
        initial_user_count = len(all_users) if all_users is not None else 0
        n_of_threads = 18
        n_of_users_per_thread = 6
        self._run_transaction_multiple_threads(n_of_threads, n_of_users_per_thread)
        final_user_count = dao.get_all_users(is_count=True)
        self.assertEqual(initial_user_count + n_of_threads * n_of_users_per_thread, final_user_count, 
                         "Each of %s threads should have created %s more users to a total of %s. "
                         "Expected %s but got %s"%(n_of_threads, n_of_users_per_thread, n_of_threads * n_of_users_per_thread, 
                                                   initial_user_count + n_of_threads * n_of_users_per_thread, final_user_count))

    @transactional_test
    def test_transaction_nested(self):
        """
        A case of nested transaction. Check that if the ALLOW_NESTED_TRANSACTIONS is set to false,
        an exception is raised when a nested transaction is attempted. This will be default behaviour in TVB, only
        overwritten for transactional tests.
        """    
        cfg.ALLOW_NESTED_TRANSACTIONS = False
        try:
            self.assertRaises(NestedTransactionUnsupported, self._store_users_nested, 4, self._store_users_happy_flow)
        finally:
            cfg.ALLOW_NESTED_TRANSACTIONS = True

    def _run_transaction_multiple_threads(self, n_of_threads, n_of_users_per_thread):
        """
        Spawn a number of threads each storing a number of users. Wait on them by joining.
        """
        for idx in xrange(n_of_threads):
            th = threading.Thread(target=self._store_users_happy_flow, args=(n_of_users_per_thread,), 
                                  kwargs={'prefix' : str(idx)})
            th.start()
            
        for t in threading.enumerate():
            if t is threading.currentThread():
                continue
            t.join()


    @add_session
    def _dao_add_user_forget_commit(self):
        """
        Test use case where you add user but forget to commit. This should be handled automatically.
        """
        self.session.add(model.User('username', 'password', 'mail', True, 'role'))
        
    @add_session
    def _dao_change_user_forget_commit(self, user_id, new_name):
        """
        Test use case where you add user but forget to commit. This should be handled automatically.
        """
        user = self.session.query(model.User).filter(model.User.id == user_id).one()
        user.username = new_name
        
    @add_session
    def _dao_delete_user_forget_commit(self, user_id):
        """
        Test use case where you add user but forget to commit. This should be handled automatically.
        """
        user = self.session.query(model.User).filter(model.User.id == user_id).one()
        self.session.delete(user)
    
    @add_session
    def _dao_add_user_raise_ex(self, n_users):
        """
        A dao method that is not marked transactional. Even if exception is raised the added user should be 
        present in database unless this is part of a parent transaction that is rolled back by it.
        """
        self.session.add(model.User('username', 'password', 'mail', True, 'role'))
        self.session.commit()
        raise Exception("Just to trigger session level rollback instead of transaction level rollback.")

    @transactional
    def _store_users_nested(self, n_users, inner_trans_func):
        """
        This method stores n_users, after which it calls inner_trans_func with n_users as parameter. At the end it raises an exception so
        transaction will fail. All changes should be reverted regardless if inner_trans_func succedes or fails.
        
        @param n_users: number of users to be stored both by this method and by the passed inner_trans_func
        @param inner_trans_func: either _store_users_happy_flow or _store_users_raises_exception
        """
        for idx in range(n_users):
            TestFactory.create_user('test_user_nested' + str(idx), 'pass', 'test@test.test', True, 'test')
        inner_trans_func(n_users)
        raise Exception("This is just so transactional kicks in and a rollback should be done.")
    
    @transactional
    def _store_users_happy_flow(self, n_users, prefix=""):
        """
        Store users in happy flow. In this case the transaction should just be commited properly and changes
        should be visible in database.
        
        @param n_users: number of users to be stored by this method
        """
        for idx in range(n_users):
            TestFactory.create_user(prefix + 'test_user' + str(idx), 'pass', 'test@test.test', True, 'test')
    
    
    @transactional
    def _store_users_raises_exception(self, n_users):
        """
        Store users but at the end raise an exception. In case the exception is not handled up until the
        transactional decorator, all changes should be rolled back.
        
        @param n_users: number of users to be stored by this method
        """
        for idx in range(n_users):
            TestFactory.create_user('test_user' + str(idx), 'pass', 'test@test.test', True, 'test')
        raise Exception("This is just so transactional kicks in and a rollback should be done.")
        

def suite():
    """
        Gather all the tests in a test suite.
    """
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(TransactionalTests))
    return test_suite


if __name__ == "__main__":
    #So you can run tests from this package individually.
    unittest.main()   
