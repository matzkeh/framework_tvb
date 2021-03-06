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
.. moduleauthor:: Lia Domide <lia.domide@codemart.ro>
.. moduleauthor:: Bogdan Neacsa <bogdan.neacsa@codemart.ro>
"""
import json
import math
import numpy
import pylab
from copy import copy
from tvb.basic.config.settings import TVBSettings as config
from tvb.core.adapters.abcdisplayer import ABCDisplayer
from tvb.core.adapters.exceptions import LaunchException
from tvb.basic.filters.chain import FilterChain
from tvb.core.entities.storage import dao
from tvb.datatypes.connectivity import Connectivity
from tvb.datatypes.graph import ConnectivityMeasure
from tvb.datatypes.surfaces import CorticalSurface, RegionMapping
from tvb.datatypes.projections import ProjectionRegionEEG


class ConnectivityViewer(ABCDisplayer):
    """ 
    Given a Connectivity Matrix and a Surface data the viewer will display the matrix 'inside' the surface data. 
    The surface is only displayed as a shadow.
    """
    
    def get_input_tree(self):
        """
        Take as Input a Connectivity Object.
        """
        return [{'name': 'input_data', 'label': 'Connectivity Matrix', 'type' : Connectivity, 'required': True},
                {'name': 'surface_data', 'label': 'Brain Surface', 'type' : CorticalSurface, 
                  'description': 'The Brain Surface is used to give you an idea of the connectivity position relative to the full '
                                 'brain cortical surface.  This surface will be displayed as a shadow (only used in 3D Edges viewer).'},
                {'name':'colors', 'label':'Node Colors','type': ConnectivityMeasure,
                 'conditions': FilterChain(fields = [FilterChain.datatype + '._nr_dimensions'], operations = ["=="], values = [1]),
                 'description' : 'A ConnectivityMesure datatype that establishes a colormap for the nodes displayed in the 2D Connectivity viewers.'},
                {'name':'step', 'label': 'Color Threshold', 'type': 'float', 
                 'description': 'All nodes with a value greater than this threshold will be displayed as red discs, otherwise they will be yellow. (This applies to 2D Connectivity Viewers and the threshold will depend on the metric used to set the Node Color)'},
                {'name': 'rays', 'label': 'Shapes Dimensions', 'type': ConnectivityMeasure,
                 'conditions': FilterChain(fields = [FilterChain.datatype + '._nr_dimensions'], operations = ["=="], values = [1]),
                 'description' : 'A ConnectivityMeasure datatype used to establish the size of the spheres representing each node. (It only applies to 3D Nodes viewer).'}]


    def get_required_memory_size(self, input_data, surface_data, colors, rays, step):
        """
        Return the required memory to run this algorithm.
        """
        if surface_data is not None:
            # Nr of triangles * sizeOf(uint16) + (nr of vertices + nr of normals) * sizeOf(float)
            return surface_data.number_of_vertices * 6 * 4 + surface_data.number_of_vertices * 6 * 8
        # If no surface pass, assume enough memory should be available.
        return -1

    def launch(self, input_data, surface_data=None, colors=None, rays=None, step=None):
        """
        Given the input connectivity data and the surface data, 
        build the HTML response to be displayed.
        """
        global_params, global_pages = self.compute_connectivity_global_params(input_data, surface_data)
        global_params['isSingleMode'] = False
        
        result_params, result_pages = Connectivity2DViewer().compute_parameters( input_data, colors, rays, step)
        result_params.update(global_params)
        result_pages.update(global_pages)
        _params, _pages = Connectivity3DViewer().compute_parameters( input_data, colors, rays)
        result_params.update(_params)
        result_pages.update(_pages)
        _params, _pages = MPLH5Connectivity().compute_parameters( input_data)
        result_params.update(_params)
        result_pages.update(_pages)
        result_params[self.EXPORTABLE_FIGURE] = True
        return self.build_display_result("connectivity/main_connectivity", result_params, result_pages)


    def generate_preview(self, input_data, figure_size=None, surface_data=None, colors=None, rays=None, step=None):
        """
        Generate the preview for the BURST cockpit.
        """
        parameters, _ = Connectivity2DViewer().compute_preview_parameters(input_data, figure_size[0], figure_size[1], 
                                                                          colors, rays, step)
        return self.build_display_result("connectivity/portlet_preview", parameters, {})


    def submit_connectivity(self, original_connectivity, new_weights, interest_area_indexes, **_):
        """
        Method to be called when user submits changes on the 
        Connectivity matrix in the Visualizer.
        """
        result = []
        conn = self.load_entity_by_gid(original_connectivity)
        result_connectivity = conn.generate_new_connectivity(new_weights, interest_area_indexes, self.storage_path)
        result.append(result_connectivity)
        
        linked_region_mappings = dao.get_generic_entity(RegionMapping, original_connectivity, '_connectivity')
        for mapping in linked_region_mappings:
            result.append(mapping.generate_new_region_mapping(result_connectivity.gid, self.storage_path))
            
        linked_projection = dao.get_generic_entity(ProjectionRegionEEG, original_connectivity, '_sources')
        for projection in linked_projection:
            result.append(projection.generate_new_projection(result_connectivity.gid, self.storage_path))
        return result


    def compute_connectivity_global_params(self, input_data, surface_data=None):
        """
        Returns a dictionary which contains the data needed for drawing a connectivity.
        """
        path_weights = self.paths2url(input_data, 'weights')
        path_pos = self.paths2url(input_data, 'centres')
        path_tracts = self.paths2url(input_data, 'tract_lengths')

        if surface_data:
            url_vertices, url_normals, url_triangles = surface_data.get_urls_for_rendering()
        else:
            url_vertices = []
            url_triangles = []
            url_normals = []

        # compute the alpha value of the surface based on the number of vertices
        # for 16384 vertices a good alpha value is 0.05
        # todo: find a better way to compute the alpha
        alpha_value = 0.05
        landmark = 16384
        if surface_data and surface_data.number_of_vertices < landmark:
            alpha_value = 0.05 * landmark / surface_data.number_of_vertices

        submit_url = self.get_submit_method_url("submit_connectivity")
        global_pages = dict(controlPage = "connectivity/top_right_controls")

        minimum = min([min(data) for data in input_data.weights])
        maximum = max([max(data) for data in input_data.weights])

        minimum_t = min([min(data) for data in input_data.tract_lengths])
        maximum_t = max([max(data) for data in input_data.tract_lengths])
        
        global_params = dict(urlWeights= path_weights, urlPositions = path_pos, urlTracts= path_tracts,
                             originalConnectivity = input_data.gid, title="Connectivity Control",
                             submitURL = submit_url,
                             positions = input_data.centres, weights = input_data.weights,
                             tractsMin = json.dumps(minimum_t), tractsMax = json.dumps(maximum_t),
                             weightsMin = json.dumps(minimum), weightsMax = json.dumps(maximum),
                             pointsLabels = input_data.region_labels,
                             urlVertices = json.dumps(url_vertices), urlTriangles = json.dumps(url_triangles),
                             urlNormals = json.dumps(url_normals), alpha_value = alpha_value,
                             connectivity_nose_correction = json.dumps( input_data.nose_correction),
                             connectivity_entity = input_data, surface_entity = surface_data,
                             algo_group = self.get_algo_group(),
                             base_selection = input_data.saved_selection_labels)
        return global_params, global_pages
    
#    
# -------------------- Connectivity 3D code starting -------------------

class Connectivity3DViewer():
    """
    Behavior for the HTML/JS 3D representation of the connectivity matrix.
    """
    
    @staticmethod
    def compute_parameters(input_data, colors = None, rays = None):
        """
        Having as inputs a Connectivity matrix(required) and two arrays that 
        represent the rays and colors of the nodes from the matrix(optional) 
        this method will build the required parameter dictionary that will be 
        sent to the HTML/JS 3D representation of the connectivity matrix.
        """
        if colors is not None:
            color_list = colors.array_data.tolist()
            color_list = ABCDisplayer.get_one_dimensional_list(color_list, input_data.number_of_regions, 
                                                               "Invalid input size for Sphere Colors")
            color_list = numpy.nan_to_num(color_list).tolist()
        else:
            color_list = [1.0] * input_data.number_of_regions
            
        if rays is not None:
            rays_list = rays.array_data.tolist()
            rays_list = ABCDisplayer.get_one_dimensional_list(rays_list, input_data.number_of_regions, 
                                                              "Invalid input size for Sphere Sizes")
            rays_list = numpy.nan_to_num(rays_list).tolist()
        else:
            rays_list = [1.0] * input_data.number_of_regions
            
        params = dict(raysArray = json.dumps(rays_list), rayMin = min(rays_list), rayMax = max(rays_list),
                      colorsArray = json.dumps(color_list), colorMin = min(color_list), colorMax = max(color_list))
        return params, {}

    
# -------------------- Connectivity 2D code starting  ------------------
X_CANVAS_SMALL = 280
Y_CANVAS_SMALL = 145
X_CANVAS_FULL = 280
Y_CANVAS_FULL = 300


class Connectivity2DViewer():
    """
    Having as inputs a Connectivity matrix(required) and two arrays that 
    represent the colors and shapes of the nodes from the matrix(optional) 
    the viewer will build the required parameter dictionary that will be 
    sent to the HTML/JS 2D representation of the connectivity matrix.
    """
    DEFAULT_COLOR = '#cc0000'
    OTHER_COLOR = '#ffff00'
    MIN_RAY = 4
    MAX_RAY = 40
    MIN_WEIGHT_VALUE = 0.0
    MAX_WEIGHT_VALUE = 0.6            


    def compute_parameters(self, input_data, colors=None, rays=None, step=None):
        """
        Build the required HTML response to be displayed.
        """
        if input_data.number_of_regions <= 3:
            raise LaunchException('The connectivity matrix you selected has fewer nodes than acceptable for display!')
        
        half = input_data.number_of_regions / 2
        normalized_weights = self._normalize_weights(input_data.weights)
        weights = Connectivity2DViewer._get_weights(normalized_weights)
        
        ## Compute shapes and colors ad adjacent data
        norm_rays, min_ray, max_ray = self._normalize_rays(rays, input_data.number_of_regions)
        colors, step = self._prepare_colors(colors, input_data.number_of_regions, step)
        
        right_json = self._get_json(input_data.region_labels[half:], input_data.centres[half:], weights[1], math.pi, 
                                    1, 2, norm_rays[half:], colors[half:], X_CANVAS_SMALL, Y_CANVAS_SMALL)
        left_json = self._get_json(input_data.region_labels[:half], input_data.centres[:half], weights[0], math.pi, 
                                   1, 2, norm_rays[:half], colors[:half], X_CANVAS_SMALL, Y_CANVAS_SMALL)
        full_json = self._get_json(input_data.region_labels, input_data.centres, input_data.weights, math.pi, 
                                   0, 1, norm_rays, colors, X_CANVAS_FULL, Y_CANVAS_FULL)
        
        params = dict(bothHemisphereJson = full_json, rightHemisphereJson = right_json, leftHemisphereJson = left_json,
                      stepValue = step or max_ray, firstColor = self.DEFAULT_COLOR,
                      secondColor = self.OTHER_COLOR, minRay = min_ray, maxRay = max_ray)
        return params, {}
    
    
    def compute_preview_parameters(self, input_data, width, height, colors=None, rays=None, step=None):
        """
        Build the required HTML response to be displayed in the BURST preview iFrame.
        """
        if input_data.number_of_regions <= 3:
            raise LaunchException('The connectivity matrix you selected has fewer nodes than acceptable for display!')
        norm_rays, min_ray, max_ray = self._normalize_rays(rays, input_data.number_of_regions)
        colors, step = self._prepare_colors(colors, input_data.number_of_regions, step)
        normalizer_size_coeficient = width / 600.0
        if (height / 700 < normalizer_size_coeficient):
            normalizer_size_coeficient = (height * 0.8) / 700.0
        x_size = X_CANVAS_FULL * normalizer_size_coeficient
        y_size = Y_CANVAS_FULL * normalizer_size_coeficient
        full_json = self._get_json(input_data.region_labels, input_data.centres, input_data.weights, math.pi, 0, 1,
                                   norm_rays, colors, x_size, y_size)
        params = dict(bothHemisphereJson = full_json, stepValue = step or max_ray, firstColor = self.DEFAULT_COLOR,
                      secondColor = self.OTHER_COLOR, minRay = min_ray, maxRay = max_ray)
        return params, {}

    def _get_json(self, labels, positions, weights, rotate_angle, coord_idx1,
                 coord_idx2, dimensions_list, colors_list, x_canvas, y_canvas):
        """
        Method used for creating a valid JSON for an entire chart.
        """
        result_json = '['
        max_y = max(positions[:, coord_idx2])
        min_y = min(positions[:, coord_idx2])
        max_x = max(positions[:, coord_idx1])
        min_x = min(positions[:, coord_idx1])
        y_scale = 2 * y_canvas/(max_y - min_y)
        x_scale = 2 * x_canvas/(max_x - min_x)
        mid_x_value = (max_x + min_x) / 2
        mid_y_value = (max_y + min_y) / 2
        for i in range(len(positions)):
            result_json = result_json + self.point2json(labels[i], (positions[i][coord_idx1] - mid_x_value) * x_scale,
                                                        (positions[i][coord_idx2] - mid_y_value) * y_scale,
                                                        Connectivity2DViewer.get_adjacencies_json(weights[i], labels),
                                                        rotate_angle, dimensions_list[i], colors_list[i])
            if i != len(positions) - 1:
                result_json = result_json + ','
        return result_json + ']'


    @classmethod
    def _get_weights(cls, weights):
        """
        Method used for calculating the weights for the right and for the 
        left hemispheres. Those matrixes are obtained from
        a weights matrix which contains data related to both hemispheres.
        """
        half = len(weights)/2
        l_aux, r_aux = weights[:half], weights[half:]
        r_weights = []
        l_weights = []
        for i in range(half):
            l_weights.append(l_aux[i][:half])
        for i in range(half, len(weights)):
            r_weights.append(r_aux[i - half][half:])
        return l_weights, r_weights
    

    def point2json(self, node_lbl, x_coord, y_coord, adjacencies, angle, shape_dimension, shape_color):
        """
        Method used for creating a valid JSON for a certain point.
        """
        form = "circle"
        default_dimension = 6
        angle = math.atan2(y_coord, x_coord) + angle
        radius = math.sqrt(math.pow(x_coord, 2) + math.pow((y_coord), 2))
        
        result_json = "{\"id\": \"" + node_lbl + "\"," + "\"name\": \"" + node_lbl + "\","
        result_json = result_json + "\"data\": {"
        result_json = result_json + "\"$dim\": " + str(default_dimension) + ","
        result_json = result_json + "\"$type\": \"" + form + "\","
        result_json = result_json + "\"$color\":\"" + self.DEFAULT_COLOR + "\","
        result_json = result_json + "\"customShapeDimension\": " + str(shape_dimension) + ","
        result_json = result_json + "\"customShapeColor\": \"" + str(shape_color) + "\","
        result_json = result_json + "\"angle\": " + str(angle) + ","
        result_json = result_json + "\"radius\": " + str(radius)
        result_json = result_json + "},"
        result_json = result_json + "\"adjacencies\": [" + adjacencies + "] }"
        return result_json


    @classmethod
    def get_adjacencies_json(cls, point_weights, points_labels):
        """
        Method used for obtaining a valid JSON which will contain all the edges of a certain node.
        """
        adjacencies = ""
        for i in range(len(point_weights)):
            weight = point_weights[i]
            if weight:
                if len(adjacencies) > 0:
                    adjacencies = adjacencies + ","
                adjacencies = adjacencies + "{ \"nodeTo\": \"" + points_labels[i]
                adjacencies = adjacencies + "\"," + "\"data\": { \"weight\": " + str(weight) + "}}"
        return adjacencies
    
    
    def _prepare_colors(self, colors, expected_size, step=None):
        """
        From the input array, all values smaller than step will get a different color
        """
        if colors is None:
            return [self.DEFAULT_COLOR] * expected_size, None
        colors = numpy.nan_to_num(colors.array_data).tolist()
        colors = ABCDisplayer.get_one_dimensional_list(colors, expected_size, "Invalid size for colors array!")
        result = []
        if step is None:
            step = (max(colors) + min(colors)) /2
        for val in colors:
            if val < step:
                result.append(self.OTHER_COLOR)
            else:
                result.append(self.DEFAULT_COLOR)
        return result, step
    
    
    def _normalize_rays(self, rays, expected_size):
        """
        Make sure all rays are in the interval [self.MIN_RAY, self.MAX_RAY]
        """
        if rays is None:
            value = (self.MAX_RAY+ self.MIN_RAY)/2
            return [value] * expected_size, value, value
        rays = rays.array_data.tolist()
        rays = ABCDisplayer.get_one_dimensional_list(rays, expected_size, "Invalid size for rays array.")
        min_x = min(rays)
        max_x = max(rays)
        if min_x >= self.MIN_RAY and max_x <= self.MAX_RAY:
            # No need to normalize
            return rays, min_x, max_x
        result = []
        diff = max_x-min_x
        if min_x == max_x:
            diff = self.MAX_RAY - self.MIN_RAY
        for ray in rays:
            result.append(self.MIN_RAY + self.MAX_RAY*(ray-min_x)/diff)
        result = numpy.nan_to_num(result).tolist()
        return result, min(rays), max(rays)
    

    def _normalize_weights(self, weights):
        """
        Normalize the weights matrix. The values should be between 
        MIN_WEIGHT_VALUE and MAX_WEIGHT_VALUE
        """
        weights = copy(weights)
        min_value = numpy.min(weights)
        max_value = numpy.max(weights)
        if (min_value < self.MIN_WEIGHT_VALUE or 
            max_value > self.MAX_WEIGHT_VALUE):
            for i in range(len(weights)):
                for j in range(len(weights[i])):
                    if min_value == max_value:
                        weights[i][j] = self.MAX_WEIGHT_VALUE
                    else:
                        weights[i][j] = (self.MIN_WEIGHT_VALUE + ((weights[i][j] - min_value) / (max_value - min_value))
                                        * (self.MAX_WEIGHT_VALUE - self.MIN_WEIGHT_VALUE))
        return weights

                
# -------------------- Connectivity MPLH5 code starting  ------------------

class MPLH5Connectivity():
    """
    MPLH5 tab page, where the entire connectivity matrix can be seen.
    """
      
    @staticmethod             
    def compute_parameters(input_data):
        """
        Build the required HTML response to be displayed.
        """
        figure = pylab.figure(figsize=(7, 8))
        pylab.clf()
        
        matrix = input_data.weights
        matrix_size = input_data.number_of_regions
        labels = input_data.region_labels
        plot_title = "Connection Strength"
        
        order = numpy.arange(matrix_size)
        # Assumes order is shape (number_of_regions, )
        order_rows = order[:, numpy.newaxis]
        order_columns = order_rows.T

        axes = figure.gca()
        img = axes.matshow(matrix[order_rows, order_columns])
        axes.set_title(plot_title) 
        figure.colorbar(img)
        
        if (labels is None):
            return
        
        axes.set_yticks(numpy.arange(matrix_size))
        axes.set_yticklabels(list(labels[order]), fontsize=8)
        axes.set_xticks(numpy.arange(matrix_size))
        axes.set_xticklabels(list(labels[order]), fontsize=8, rotation=90)
        
        figure.canvas.draw() 
        parameters = dict(serverIp=config.SERVER_IP, serverPort=config.MPLH5_SERVER_PORT, figureNumber=figure.number,
                          showFullToolbar=False)
        return parameters, {}
    
    
    