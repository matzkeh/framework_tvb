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
Adapter that uses the traits module to generate interfaces for ... Analyzer.

.. moduleauthor:: Stuart A. Knock <Stuart@tvb.invalid>
.. moduleauthor:: Lia Domide <lia.domide@codemart.ro>

"""
import numpy
from tvb.basic.config.settings import TVBSettings
from tvb.analyzers.cross_correlation import CrossCorrelate
from tvb.core.adapters.abcadapter import ABCAsynchronous
from tvb.basic.filters.chain import FilterChain
from tvb.basic.traits.util import log_debug_array
from tvb.datatypes.time_series import TimeSeries
from tvb.datatypes.temporal_correlations import CrossCorrelation
from tvb.basic.logger.builder import get_logger

LOG = get_logger(__name__)


class CrossCorrelateAdapter(ABCAsynchronous):
    """ TVB adapter for calling the CrossCorrelate algorithm. """
    
    _ui_name = "Cross-correlation of nodes"
    _ui_description = "Cross-correlate two one-dimensional arrays."
    _ui_subsection = "crosscorr"
    
    
    def get_input_tree(self):
        """
        Return a list of lists describing the interface to the analyzer. This
        is used by the GUI to generate the menus and fields necessary for
        defining a simulation.
        """
        algorithm = CrossCorrelate()
        algorithm.trait.bound = self.INTERFACE_ATTRIBUTES_ONLY
        tree = algorithm.interface[self.INTERFACE_ATTRIBUTES]
        tree[0]['conditions'] = FilterChain(fields = [FilterChain.datatype + '._nr_dimensions'], operations = ["=="], values = [4])
        return tree
    
    
    def get_output(self):
        return [CrossCorrelation]
    
    def configure(self, time_series):
        """
        Store the input shape to be later used to estimate memory usage. Also
        create the algorithm instance.
        """
        self.input_shape = time_series.read_data_shape()
        log_debug_array(LOG, time_series, "time_series")
        
        ##-------------------- Fill Algorithm for Analysis -------------------##
        self.algorithm = CrossCorrelate()
        
    
    def get_required_memory_size(self, **kwargs):
        """
        Returns the required memory to be able to run the adapter.
        """
        #Not all the data is loaded into memory at one time here.
        used_shape = (self.input_shape[0], 1, self.input_shape[2], self.input_shape[3])
        input_size = numpy.prod(used_shape) * 8.0
        output_size = self.algorithm.result_size(used_shape)
        return input_size + output_size
    
    def get_required_disk_size(self, **kwargs):
        """
        Returns the required disk size to be able to run the adapter (in kB).
        """
        used_shape = (self.input_shape[0], 1, self.input_shape[2], self.input_shape[3])
        return self.algorithm.result_size(used_shape) * TVBSettings.MAGIC_NUMBER / 8 / 2 ** 10
    
    def launch(self, time_series):
        """ 
        Launch algorithm and build results. 
        """
        ##--------- Prepare a CrossCorrelation object for result ------------##
        cross_corr = CrossCorrelation(source = time_series,
                                      storage_path = self.storage_path)
        
        node_slice = [slice(self.input_shape[0]), None, slice(self.input_shape[2]), slice(self.input_shape[3])]
        ##---------- Iterate over slices and compose final result ------------##
        small_ts = TimeSeries(use_storage=False)
        small_ts.sample_period = time_series.sample_period
        for var in range(self.input_shape[1]):
            node_slice[1] = slice(var, var + 1)
            small_ts.data = time_series.read_data_slice(tuple(node_slice))
            self.algorithm.time_series = small_ts
            partial_cross_corr = self.algorithm.evaluate()
            cross_corr.write_data_slice(partial_cross_corr)
        cross_corr.time = partial_cross_corr.time
        cross_corr.labels_ordering[1] = time_series.labels_ordering[2]
        cross_corr.labels_ordering[2] = time_series.labels_ordering[2]
        cross_corr.close_file()
        return cross_corr


