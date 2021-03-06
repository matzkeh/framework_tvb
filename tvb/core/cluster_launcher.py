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
This module is called in a new process by the rpserver:
Example: python cluster_launcher.py 4 user_name_label
4 is the operation id stored in the DataBase in the table "OPERATIONS"
It gets the algorithm, and the adapter with its parameters from database.
And finally launches the computation.
The results of the computation will be stored by the adapter itself.

.. moduleauthor:: Bogdan Neacsa <bogdan.neacsa@codemart.ro>
.. moduleauthor:: Lia Domide <lia.domide@codemart.ro>
.. moduleauthor:: Yann Gordon <yann@tvb.invalid>

"""

## Make sure selected profile is propagated when launching an operation.
import sys
from tvb.basic.profile import TvbProfile as tvb_profile
tvb_profile.set_profile(sys.argv)

### Overwrite PostgreSQL number of connections when executed in the context of a node
from tvb.basic.config.settings import TVBSettings
TVBSettings.MAX_DB_CONNECTIONS = TVBSettings.MAX_DB_ASYNC_CONNECTIONS
TVBSettings.OPERATION_EXECUTION_PROCESS = True


import matplotlib
from tvb.basic.logger.builder import get_logger
from tvb.core.adapters.abcadapter import ABCAdapter
from tvb.core.entities.storage import dao
from tvb.core.utils import parse_json_parameters
from tvb.core.traits import db_events
from tvb.core.services.operationservice import OperationService
from tvb.core.services.workflowservice import WorkflowService


LOGGER = get_logger('tvb.core.cluster_launcher')
matplotlib.use('module://tvb.interfaces.web.mplh5.mplh5_backend')



def do_operation_launch(operation_id):
    """
    Event attached to the local queue for executing an operation, when we will have resources available.
    """
    try:
        LOGGER.debug("Loading operation with id=%s"%(operation_id,))
        curent_operation = dao.get_operation_by_id(operation_id)
        algorithm = curent_operation.algorithm
        algorithm_group = dao.get_algo_group_by_id(algorithm.fk_algo_group)
        LOGGER.debug("Importing Algorithm: "+str(algorithm_group.classname)+" for Operation:"+str(curent_operation.id))
        PARAMS = parse_json_parameters(curent_operation.parameters)
        adapter_instance = ABCAdapter.build_adapter(algorithm_group)
        
        ## Un-comment bellow for profiling an operation:
        ## import cherrypy.lib.profiler as profiler
        ## p = profiler.Profiler("/Users/lia.domide/TVB/profiler/")
        ## p.run(OperationService().initiate_prelaunch, curent_operation, adapter_instance, {}, **PARAMS)
        
        OperationService().initiate_prelaunch(curent_operation, adapter_instance, {}, **PARAMS)
        LOGGER.debug("Successfully finished operation "+ str(operation_id))
        
    except Exception, excep:
        LOGGER.error("Could not execute operation " + str(sys.argv[1]))
        LOGGER.exception(excep)
        parent_burst = dao.get_burst_for_operation_id(operation_id)
        if parent_burst is not None:
            WorkflowService().mark_burst_finished(parent_burst, error=True, error_message=str(excep))
    
    
if __name__ == '__main__':
    OPERATION_ID = sys.argv[1]
    # Make sure DB events are linked.
    db_events.attach_db_events()
    do_operation_launch(OPERATION_ID)
    sys.exit(0)
    

