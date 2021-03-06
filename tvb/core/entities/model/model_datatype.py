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
Entities for Generic DataTypes, Links and Groups of DataTypes are defined here.

.. moduleauthor:: Lia Domide <lia.domide@codemart.ro>
.. moduleauthor:: Bogdan Neacsa <bogdan.neacsa@codemart.ro>
.. moduleauthor:: Yann Gordon <yann@tvb.invalid>
"""

from datetime import datetime
from copy import copy
from sqlalchemy.orm import relationship, backref
from tvb.core.utils import generate_guid
from sqlalchemy import Boolean, Integer, String, Column, ForeignKey, DateTime
from tvb.core.entities.model.model_base import Base
from tvb.core.entities.model.model_project import Project
from tvb.core.entities.model.model_operation import Operation, OperationGroup
from tvb.core.entities.model.model_burst import BurstConfiguration
from tvb.basic.logger.builder import get_logger


LOG = get_logger(__name__)


FILTER_CATEGORIES = {'model.DataType.subject': {'display': 'Subject', 'type': 'string',
                                                'operations': ['!=', '==', 'like', 'in', 'not in'] },
                     'model.DataType.state': {'display': 'State', 'type': 'string',
                                              'operations': ['!=', '==', 'in', 'not in'] },
                     'model.DataType.disk_size': {'display': 'Disk Size (KB)', 'type': 'int',
                                                  'operations': ['<', '==', '>'] },
                     'model.DataType.user_tag_1': {'display': 'Tag 1', 'type': 'string',
                                                   'operations': ['!=', '==', 'like'] },
                     'model.DataType.user_tag_2': {'display': 'Tag 2', 'type': 'string',
                                                   'operations': ['!=', '==', 'like'] },
                     'model.DataType.user_tag_3': {'display': 'Tag 3', 'type': 'string',
                                                   'operations': ['!=', '==', 'like'] },
                     'model.DataType.user_tag_4': {'display': 'Tag 4', 'type': 'string',
                                                   'operations': ['!=', '==', 'like'] },
                     'model.DataType.user_tag_5': {'display': 'Tag 5', 'type': 'string',
                                                   'operations': ['!=', '==', 'like'] },
                     'model.Operation.start_date': {'display': 'Start date', 'type': 'date',
                                                    'operations':['==', '!=', '<', '>']},
                     'model.BurstConfiguration.name': {'display': 'Burst Name', 'type': 'string',
                                                       'operations':['==', '!=', 'like']},
                     'model.Operation.completion_date': {'display': 'Completion date', 'type': 'date',
                                                         'operations':['==', '!=', '<', '>']}}


class DataType(Base):
    """ 
    Base class for DB storage of Types.
    DataTypes, are the common language between Visualizers, 
    Simulator and Analyzers.

    """
    __tablename__ = 'DATA_TYPES'
    id = Column(Integer, primary_key=True)
    gid = Column(String, unique=True)
    type = Column(String)    # Name of class inheriting from current type
    module = Column(String)
    subject = Column(String)
    state = Column(String)   # RAW, INTERMEDIATE, FINAL
    visible = Column(Boolean, default=True)
    invalid = Column(Boolean, default=False)
    is_nan = Column(Boolean, default=False)
    create_date = Column(DateTime, default=datetime.now)
    disk_size = Column(Integer)
    user_tag_1 = Column(String)     # Name used by framework and perpetuated from a DataType to derived entities.
    user_tag_2 = Column(String)
    user_tag_3 = Column(String)
    user_tag_4 = Column(String)
    user_tag_5 = Column(String)
    
    # ID of a burst in which current dataType was generated
    # Native burst-results are referenced from a workflowSet as well
    # But we also have results generated afterwards from TreeBurst tab.
    fk_parent_burst = Column(Integer, ForeignKey('BURST_CONFIGURATIONS.id')) 
    _parent_burst = relationship(BurstConfiguration, backref=backref("DATA_TYPES", order_by=id))
                                      
    #it should be a reference to a DataTypeGroup, but we can not create that FK
    #because this two tables (DATA_TYPES, DATA_TYPES_GROUPS) will reference each
    #other mutually and SQL-Alchemy complains about that.
    fk_datatype_group = Column(Integer, ForeignKey('DATA_TYPES.id'))

    fk_from_operation = Column(Integer, ForeignKey('OPERATIONS.id', ondelete="CASCADE"))
    parent_operation = relationship(Operation, backref=backref("DATA_TYPES", order_by=id, cascade="all,delete"))
    
    
    def __init__(self, gid=None, **kwargs):

        if gid is None:
            self.gid = generate_guid()
        else:
            self.gid = gid
        self.type = self.__class__.__name__
        self.module = self.__class__.__module__
        
        try:
            self.__initdb__(**kwargs)
        except Exception as exc:
            LOG.warning('Could not perform __initdb__: %r', exc)
        super(DataType, self).__init__()


    def __initdb__(self, subject='', state=None, operation_id=None, fk_parent_burst=None, disk_size=None,
                   user_tag_1=None, user_tag_2=None, user_tag_3=None, user_tag_4=None, user_tag_5=None, **_):
        """Set attributes"""
        self.subject = subject
        self.state = state
        self.fk_from_operation = operation_id
        self.user_tag_1 = user_tag_1
        self.user_tag_2 = user_tag_2
        self.user_tag_3 = user_tag_3
        self.user_tag_4 = user_tag_4
        self.user_tag_5 = user_tag_5
        self.disk_size = disk_size
        self.fk_parent_burst = fk_parent_burst


    @property
    def display_name(self):
        """
        To be implemented in each sub-class which is about to be displayed in UI, 
        and return the text to appear.
        """
        name = self.type
        for tag in [self.user_tag_1, self.user_tag_2, self.user_tag_3, self.user_tag_4, self.user_tag_5]:
            if tag is not None and len(tag) > 0:
                name = name + " - " + str(tag)
        return name

    def __repr__(self):
        return "<DataType(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)>" % ( str(self.id), 
                        self.gid, self.type, self.module, self.subject, self.state, str(self.fk_parent_burst), 
                        self.user_tag_1, self.user_tag_2, self.user_tag_3, self.user_tag_4, self.user_tag_5)


    @staticmethod
    def accepted_filters():
        """
        Return accepted UI filters for current DataType.
        """
        return copy(FILTER_CATEGORIES)
    
    
    def persist_full_metadata(self):
        """
        Do nothing here. We will implement this only in MappedType.
        """
        pass


class DataTypeGroup(DataType):
    """
    All the datatypes resulted from an operation group 
    will be part from a datatype group.
    """
    __tablename__ = 'DATA_TYPES_GROUPS'

    id = Column('id', Integer, ForeignKey('DATA_TYPES.id', ondelete="CASCADE"), primary_key=True)
    count_results = Column(Integer)
    fk_operation_group = Column(Integer, ForeignKey('OPERATION_GROUPS.id', ondelete="CASCADE"))
    
    parent_operation_group = relationship(OperationGroup, backref=backref("DATA_TYPES_GROUPS", cascade="delete"))
    

    def __init__(self, operation_group_id, **kwargs):
        super(DataTypeGroup, self).__init__(**kwargs)
        self.fk_operation_group = operation_group_id


class Links(Base):
    """
    Class used to handle shortcuts from one datatype to another project.
    """
    __tablename__ = 'LINKS'

    id = Column(Integer, primary_key=True)
    fk_to_project = Column(Integer, ForeignKey('PROJECTS.id', ondelete="CASCADE"))
    fk_from_datatype = Column(Integer, ForeignKey('DATA_TYPES.id', ondelete="CASCADE"))
    
    referenced_project = relationship(Project, backref=backref('LINKS', order_by=id, cascade = "delete, all"))
    referenced_datatype = relationship(DataType, backref=backref('LINKS', order_by=id, cascade = "delete, all"))

    def __init__(self, from_datatype, to_project):
        self.fk_from_datatype = from_datatype
        self.fk_to_project = to_project

    def __repr__(self):
        return '<Link(%d, %d)>' % (self.fk_from_datatype, self.fk_to_project)
    

class ConnectivitySelection(Base):
    """
    Interest area.
    Or subset of nodes from a Connectivity.
    """
    
    __tablename__ = "CONNECTIVITY_SELECTIONS" 
    
    id = Column(Integer, primary_key=True)
    gid = Column(String)
    ui_name = Column(String)
    selected_nodes = Column(String)
    labels = Column(String)
    fk_in_project = Column(Integer, ForeignKey('PROJECTS.id', ondelete="CASCADE"))

    def __init__(self, selected_nodes, labels, project_id, ui_name='Default'):
        self.ui_name = ui_name
        self.selected_nodes = selected_nodes
        self.labels = labels
        self.fk_in_project = project_id
        self.gid = generate_guid()

    def __repr__(self):
        return '<Selection(%s, %s)>' % (self.ui_name, self.selected_nodes)
    
    
    
    
    