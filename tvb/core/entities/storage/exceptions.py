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
Created on Jan 15, 2013

.. moduleauthor:: Bogdan Neacsa <bogdan.neacsa@codemart.ro>
'''

class BaseStorageException(Exception):
    """
    Base class for all TVB storage exceptions.
    """
    def __init__(self, message):
        Exception.__init__(self, message)
        self.message = message

    def __repr__(self):
        return self.message
    
    
class NestedTransactionUnsupported(BaseStorageException):
    """
    Nested transactions are not supported unless in testing.
    """
    def __init__(self, message):
        BaseStorageException.__init__(self, message)
        
        
class InvalidTransactionAccess(BaseStorageException):
    """
    Exception raised in case you have any faulty access to a transaction.
    """
    def __init__(self, message):
        BaseStorageException.__init__(self, message)
        
    
    