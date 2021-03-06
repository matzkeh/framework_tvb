/**
 * TheVirtualBrain-Framework Package. This package holds all Data Management, and 
 * Web-UI helpful to run brain-simulations. To use it, you also need do download
 * TheVirtualBrain-Scientific Package (for simulators). See content of the
 * documentation-folder for more details. See also http://www.thevirtualbrain.org
 *
 * (c) 2012-2013, Baycrest Centre for Geriatric Care ("Baycrest")
 *
 * This program is free software; you can redistribute it and/or modify it under 
 * the terms of the GNU General Public License version 2 as published by the Free
 * Software Foundation. This program is distributed in the hope that it will be
 * useful, but WITHOUT ANY WARRANTY; without even the implied warranty of 
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public
 * License for more details. You should have received a copy of the GNU General 
 * Public License along with this program; if not, you can download it here
 * http://www.gnu.org/licenses/old-licenses/gpl-2.0
 *
 **/

/**
 * WebGL methods "inheriting" from webGL_xx.js in static/js.
 */
var CONNECTIVITY_CANVAS_ID = "GLcanvas";

//NOTE: if <code>uColorIndex</code> has a value grater or equal to zero then the color corresponding to this index will
//      be used for drawing otherwise the color corresponding to the <code>aColorIndex</code> will be used for drawing


function initShaders() {	
	//INIT NORMAL SHADER
    basicInitShaders("shader-fs", "shader-vs");
    shaderProgram.colorAttribute = gl.getAttribLocation(shaderProgram, "aColor");
    gl.enableVertexAttribArray(shaderProgram.colorAttribute);

    shaderProgram.useLightingUniform = gl.getUniformLocation(shaderProgram, "uUseLighting");
    shaderProgram.ambientColorUniform = gl.getUniformLocation(shaderProgram, "uAmbientColor");
    shaderProgram.lightingDirectionUniform = gl.getUniformLocation(shaderProgram, "uLightingDirection");
    shaderProgram.directionalColorUniform = gl.getUniformLocation(shaderProgram, "uDirectionalColor");
    shaderProgram.alphaUniform = gl.getUniformLocation(shaderProgram, "uAlpha");
    shaderProgram.isPicking = gl.getUniformLocation(shaderProgram, "isPicking");
    shaderProgram.pickingColor = gl.getUniformLocation(shaderProgram, "pickingColor");

    shaderProgram.colorIndex = gl.getUniformLocation(shaderProgram, "uColorIndex");
    shaderProgram.colorsArray = [];
    for (var i = 0; i < COLORS.length; i++) {
        shaderProgram.colorsArray[i] = gl.getUniformLocation(shaderProgram, "uColorsArray[" + i + "]");
    }
    
}

// if you change the no of colors (add/remove) please update also the size of the uniform 'uColorsArray' from 'x-vertex'
var COLORS = [
        [1.0, 1.0, 1.0],
        [1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0],
        [1.0, 1.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.5, 0.5, 0.5],
        [0.1, 0.1, 0.1]
];

var WHITE_COLOR_INDEX = 0;
var RED_COLOR_INDEX = 1;
var BLUE_COLOR_INDEX = 2;
var YELLOW_COLOR_INDEX = 3;
var GREEN_COLOR_INDEX = 4;
var GRAY_COLOR_INDEX = 5;
var BLACK_COLOR_INDEX = 6;

// if we pass this value to the uniform <code>uColorIndex</code> than this means that we will use the color corresponding to the <code>aColorIndex</code> attribute
var NO_COLOR_INDEX = -1;

var TRI = 3;
// Size of the cube
var PS = 3.0;
// the number of the points that were read from the 'position.txt' file (no of points from the connectivity matrix)
var NO_POSITIONS;
// each point from the connectivity matrix will be drawn as a square;
// each element of this array will contains: 1) the buffer with vertices needed for drawing the square;
// 2) the buffer with normals for each vertex of the square; 3) an array index buffer needed for drawing the square.
var positionsBuffers = [];
// this list contains an array index buffer for each point from the connectivity matrix. The indices tell us between
// which points we should draw lines. All the lines that exit from a certain node.
var CONN_comingOutLinesIndices = [];
// this list contains an array index buffer for each point from the connectivity matrix. The indices tell us between
// which points we should draw lines. All the lines that enter in a certain node.
var CONN_comingInLinesIndices = [];
// represents a buffer which contains all the points from the connectivity matrix.
var positionsPointsBuffer;
// when we draw a line we have to specify the normals for the points between which the line is drawn;
// this buffer contains the normals (fake normals) for each point from the connectivity matrix.
var linesPointsNormalsBuffer;
// the index of the point that has to be highlight
var highlightedPointIndex1 = -1;
var highlightedPointIndex2 = -1;

// a buffer which contains for each point the index corresponding to the default color (white color)
var defaultColorIndexesBuffer;
// a buffer which contains for each point the index of a color that should be used for drawing it
var colorsArrayBuffer;
// this array contains a color index for each point from the connectivity matrix. The color corresponding to that index
// will be used for drawing the lines for that point
var colorsIndexes =[];

var alphaValue = 0;

var CONN_pickedIndex = -1;
var near = 0.1;
var aspect = 1;
var doPick = false;

//when this var reaches to zero => all data needed for displaying the surface are loaded
var noOfBuffersToLoad = 3;

function customKeyDown(event) {
	GL_handleKeyDown(event);
	GFUNC_updateLeftSideVisualization();
}

function customMouseDown(event) {
	GL_handleMouseDown(event, $("#" + CONNECTIVITY_CANVAS_ID));
    doPick = true;
    GFUNC_updateLeftSideVisualization();
}

function customMouseMove(event) {
	GL_handleMouseMove(event);
	GFUNC_updateLeftSideVisualization();		
}


var linesBuffer;

function initBuffers() {
    var fakeNormal_1 = [0, 0, 1];
    var fakeNormal_2 = [0, 0, -1];

    var whitePointsColorsIndex =[];

    var points = [];
    var normals = [];
    for (var i = 0; i < NO_POSITIONS; i++) {
        points = points.concat(GVAR_positionsPoints[i]);
        if (i % 2) {
            normals = normals.concat(fakeNormal_1);
        } else {
            normals = normals.concat(fakeNormal_2);
        }
        colorsIndexes = colorsIndexes.concat(COLORS[WHITE_COLOR_INDEX]);       
    }
     for (var index = 0; index < 24 ; index++){
        	whitePointsColorsIndex = whitePointsColorsIndex.concat(COLORS[WHITE_COLOR_INDEX]);
        }

    defaultColorIndexesBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, defaultColorIndexesBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(whitePointsColorsIndex), gl.STATIC_DRAW);
    defaultColorIndexesBuffer.itemSize = 3;
    defaultColorIndexesBuffer.numItems = parseInt(whitePointsColorsIndex.length);

    colorsArrayBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, colorsArrayBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(colorsIndexes), gl.STATIC_DRAW);
    colorsArrayBuffer.itemSize = 3;
    colorsArrayBuffer.numItems = parseInt(colorsIndexes.length);

    positionsPointsBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, positionsPointsBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(points), gl.STATIC_DRAW);
    positionsPointsBuffer.itemSize = 3;
    positionsPointsBuffer.numItems = parseInt(points.length / 3);

    linesPointsNormalsBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, linesPointsNormalsBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(normals), gl.STATIC_DRAW);
    linesPointsNormalsBuffer.itemSize = 3;
    linesPointsNormalsBuffer.numItems = parseInt(normals.length / 3);

    createLinesBuffer([]);
}


function displayPoints() {
    for (var i = 0; i < NO_POSITIONS; i++) {
    	// Next line was ADDED FOR PICK
        mvPickMatrix = GL_mvMatrix.dup();
        mvPushMatrix();
        gl.bindBuffer(gl.ARRAY_BUFFER, positionsBuffers[i][0]);
        gl.vertexAttribPointer(shaderProgram.vertexPositionAttribute, TRI, gl.FLOAT, false, 0, 0);
        gl.bindBuffer(gl.ARRAY_BUFFER, positionsBuffers[i][1]);
        gl.vertexAttribPointer(shaderProgram.vertexNormalAttribute, TRI, gl.FLOAT, false, 0, 0);
        gl.bindBuffer(gl.ARRAY_BUFFER, defaultColorIndexesBuffer);
        gl.vertexAttribPointer(shaderProgram.colorAttribute, defaultColorIndexesBuffer.itemSize, gl.FLOAT, false, 0, 0);

        gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, positionsBuffers[i][2]);
       GFUNC_updateContextMenu(CONN_pickedIndex, GVAR_pointsLabels[CONN_pickedIndex],
           CONN_pickedIndex >= 0 && isAnyPointChecked(CONN_pickedIndex, CONN_comingInLinesIndices[CONN_pickedIndex], 0),
           CONN_pickedIndex >= 0 && isAnyPointChecked(CONN_pickedIndex, CONN_comingOutLinesIndices[CONN_pickedIndex], 1));
        //}
        if (i == CONN_pickedIndex) {
            gl.uniform1i(shaderProgram.colorIndex, YELLOW_COLOR_INDEX);
        } else if (i == highlightedPointIndex1) {
            gl.uniform1i(shaderProgram.colorIndex, RED_COLOR_INDEX);
        } else if (i == highlightedPointIndex2) {
            gl.uniform1i(shaderProgram.colorIndex, BLUE_COLOR_INDEX);
        } else if (GFUNC_isNodeAddedToInterestArea(i)) {
            gl.uniform1i(shaderProgram.colorIndex, GREEN_COLOR_INDEX);
        } else if (GFUNC_isIndexInNodesWithPositiveWeight(i)) {
            gl.uniform1i(shaderProgram.colorIndex, BLUE_COLOR_INDEX);
        } else if (!hasPositiveWeights(i)) {
            gl.uniform1i(shaderProgram.colorIndex, BLACK_COLOR_INDEX);
        } else {
        	gl.uniform1i(shaderProgram.colorIndex, NO_COLOR_INDEX);
        }
        // End ADDED FOR PICK
        setMatrixUniforms();
        gl.drawElements(gl.TRIANGLES, 36, gl.UNSIGNED_SHORT, 0);
        mvPopMatrix();
    }
    // Next line was ADDED FOR PICK
    doPick = false;
}


/**
 * Draw the light
 */
function addLight() {
    gl.uniform1i(shaderProgram.useLightingUniform, true);
    gl.uniform3f(shaderProgram.ambientColorUniform, 0.8, 0.8, 0.7);

    var lightingDirection = Vector.create([0.85, 0.8, 0.75]);
    var adjustedLD = lightingDirection.toUnitVector().x(-1);
    var flatLD = adjustedLD.flatten();
    gl.uniform3f(shaderProgram.lightingDirectionUniform, flatLD[0], flatLD[1], flatLD[2]);
    gl.uniform3f(shaderProgram.directionalColorUniform, 0.7, 0.7, 0.7);
    gl.uniform1f(shaderProgram.alphaUniform, 1.0);
}

function addLightForCorticalSurface() {
    gl.uniform1i(shaderProgram.useLightingUniform, true);
    gl.uniform3f(shaderProgram.ambientColorUniform, 0.2, 0.2, 0.2);

    var lightingDirection = Vector.create([-0.25, -0.25, -1]);
    var adjustedLD = lightingDirection.toUnitVector().x(-1);
    var flatLD = adjustedLD.flatten();
    gl.uniform3f(shaderProgram.lightingDirectionUniform, flatLD[0], flatLD[1], flatLD[2]);
    gl.uniform3f(shaderProgram.directionalColorUniform, 0.8, 0.8, 0.8);
    gl.uniform1f(shaderProgram.alphaUniform, alphaValue);
}

function drawScene() {
	if (!doPick) {
		createLinesBuffer(getLinesIndexes());
		gl.uniform1f(shaderProgram.isPicking, 0);
		gl.uniform3f(shaderProgram.pickingColor, 1, 1, 1);
		if (GL_zoomSpeed != 0) {
	            GL_zTranslation -= GL_zoomSpeed * GL_zTranslation;
	            GL_zoomSpeed = 0;
	        }
	    gl.viewport(0, 0, gl.viewportWidth, gl.viewportHeight);
	    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
	    // View angle is 45, we want to see object from 0.1 up to 800 distance from viewer
	    aspect = gl.viewportWidth / gl.viewportHeight;
	    perspective(45, aspect , near, 800.0);
	    loadIdentity();
	    addLight();     
	
	    //draw the lines between the checked points
	    mvPushMatrix();
	    // Translate to get a good view.
	    mvTranslate([0.0, 0.0, GL_zTranslation]);
	    multMatrix(GL_currentRotationMatrix);
	    mvTranslate([GVAR_additionalXTranslationStep, GVAR_additionalYTranslationStep, 0])
	    applyConnectivityNoseCorrection();
	    _drawLines(linesBuffer);
	    mvPopMatrix();
	
	    //draw the points
	    mvPushMatrix();
	    // Translate to get a good view.
	    mvTranslate([0.0, 0.0, GL_zTranslation]);
	    multMatrix(GL_currentRotationMatrix);
	    mvTranslate([GVAR_additionalXTranslationStep, GVAR_additionalYTranslationStep, 0])
	    applyConnectivityNoseCorrection();
	    displayPoints();
	    mvPopMatrix();
	
	   ORIENTATION_draw_nose_and_ears()
	
	    // draw the brain cortical surface
	    if (noOfBuffersToLoad == 0) {
	    // Translate to get a good view.
	        mvTranslate([0.0, 0.0, GL_zTranslation]);
	        mvPushMatrix();
	        gl.blendFunc(gl.SRC_ALPHA, gl.ONE);
	        gl.enable(gl.BLEND);
	        gl.disable(gl.DEPTH_TEST);
	        addLightForCorticalSurface();
	        multMatrix(GL_currentRotationMatrix);
	        applyConnectivityNoseCorrection();
	        mvTranslate([GVAR_additionalXTranslationStep, GVAR_additionalYTranslationStep, 0])
	        drawHemispheres(gl.TRIANGLES);
	        gl.disable(gl.BLEND);
	        gl.enable(gl.DEPTH_TEST);
	        mvPopMatrix();
	    }
	   }
	   else {
	   		gl.bindFramebuffer(gl.FRAMEBUFFER, GL_colorPickerBuffer);
	   		gl.disable(gl.BLEND) 
            gl.disable(gl.DITHER)
            gl.disable(gl.FOG) 
            gl.disable(gl.LIGHTING) 
            gl.disable(gl.TEXTURE_1D) 
            gl.disable(gl.TEXTURE_2D) 
            gl.disable(gl.TEXTURE_3D) 
	   		gl.uniform1f(shaderProgram.isPicking, 1);	
	   		gl.viewport(0, 0, gl.viewportWidth, gl.viewportHeight);
	    	gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
	    	// View angle is 45, we want to see object from 0.1 up to 800 distance from viewer
	    	aspect = gl.viewportWidth / gl.viewportHeight;
	    	perspective(45, aspect , near, 800.0);
	    	loadIdentity();
	    	
	   	    if (GL_colorPickerInitColors.length == 0) {
	   			GL_initColorPickingData(NO_POSITIONS);
	   		}	 
	    	gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
	    	
			mvPushMatrix();
		    mvTranslate([0.0, 0.0, GL_zTranslation]);
		    multMatrix(GL_currentRotationMatrix);
		    mvTranslate([GVAR_additionalXTranslationStep, GVAR_additionalYTranslationStep, 0])
		    applyConnectivityNoseCorrection();   
		    
		    for (var i = 0; i < NO_POSITIONS; i++){
		    	gl.uniform3f(shaderProgram.pickingColor, GL_colorPickerInitColors[i][0], 
		    											 GL_colorPickerInitColors[i][1], 
		    											 GL_colorPickerInitColors[i][2]);
	            gl.bindBuffer(gl.ARRAY_BUFFER, positionsBuffers[i][0]);
		        gl.vertexAttribPointer(shaderProgram.vertexPositionAttribute, TRI, gl.FLOAT, false, 0, 0);
				gl.bindBuffer(gl.ARRAY_BUFFER, positionsBuffers[i][1]);
		        gl.vertexAttribPointer(shaderProgram.vertexNormalAttribute, TRI, gl.FLOAT, false, 0, 0);
		        
		        gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, positionsBuffers[i][2]);
		        setMatrixUniforms();
        		gl.drawElements(gl.TRIANGLES, 36, gl.UNSIGNED_SHORT, 0);
	         }    
	        var newPicked = GL_getPickedIndex();
			if (newPicked!= undefined) {
                CONN_pickedIndex = newPicked;
			}
		    mvPopMatrix();		 
			doPick = false;
            gl.bindFramebuffer(gl.FRAMEBUFFER, null);
            drawScene();
		}
}

/*
 * Given a list of indexes will create the buffer of elements needed to draw
 * line between the points that correspond to those indexes.
 */
function createLinesBuffer(listOfIndexes) {
	linesBuffer = getElementArrayBuffer(listOfIndexes);
}


/**
 * Used for finding the indexes of the points that are connected by an edge. The returned list is used for creating
 * an element array buffer.
 */
function getLinesIndexes() {
    var list = [];
    for (var i = 0; i < GVAR_connectivityMatrix.length; i++) {
        for (var j = 0; j < GVAR_connectivityMatrix[i].length; j++) {
            if (GVAR_connectivityMatrix[i][j] == 1) {
                list.push(i);
                list.push(j);
            }
        }
    }

    return list;
}


function highlightPoint() {
    $("td[id^='td_']").hover(
                            function () {
                                var indexes = (this.id.split("td_")[1]).split("_");
                                highlightedPointIndex1 = indexes[1];
                                highlightedPointIndex2 = indexes[2];
                            },
                            function () {
                                highlightedPointIndex1 = -1;
                                highlightedPointIndex2 = -1;
                            });
}


function _drawLines(linesVertexIndicesBuffer) {
    gl.uniform1i(shaderProgram.colorIndex, NO_COLOR_INDEX);
    gl.bindBuffer(gl.ARRAY_BUFFER, positionsPointsBuffer);
    gl.vertexAttribPointer(shaderProgram.vertexPositionAttribute, positionsPointsBuffer.itemSize, gl.FLOAT, false, 0, 0);

    gl.bindBuffer(gl.ARRAY_BUFFER, linesPointsNormalsBuffer);
    gl.vertexAttribPointer(shaderProgram.vertexNormalAttribute, linesPointsNormalsBuffer.itemSize, gl.FLOAT, false, 0, 0);

    gl.bindBuffer(gl.ARRAY_BUFFER, colorsArrayBuffer);
    gl.vertexAttribPointer(shaderProgram.colorAttribute, colorsArrayBuffer.itemSize, gl.FLOAT, false, 0, 0);

    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, linesVertexIndicesBuffer);
    setMatrixUniforms();
    gl.drawElements(gl.LINES, linesVertexIndicesBuffer.numItems, gl.UNSIGNED_SHORT, 0);
}

/**
 * Create 2 dictionaries.
 * For each index keep a list of all incoming lines in one dictionary, and all outgoing lines in the other.
 */
function initLinesIndices() {
    for (var i = 0; i < NO_POSITIONS; i++) {
    	var indexesIn = [];
    	var indexesOut = [];
	    for (var j = 0; j < NO_POSITIONS; j++) {
	        if (j != i && parseFloat(GVAR_interestAreaVariables[GVAR_selectedAreaType]['values'][i][j])) {
	            indexesOut.push(j);
	        }
	        if (j != i && parseFloat(GVAR_interestAreaVariables[GVAR_selectedAreaType]['values'][j][i])) {
	            indexesIn.push(j);
	        } 
	    }
        CONN_comingOutLinesIndices.push(indexesOut);
        CONN_comingInLinesIndices.push(indexesIn);
    }
}


function getElementArrayBuffer(indices) {
    var vertexIndices = gl.createBuffer();
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, vertexIndices);
    gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, new Uint16Array(indices), gl.STATIC_DRAW);
    vertexIndices.itemSize = 1;
    vertexIndices.numItems = indices.length;

    return vertexIndices;
}

var selectedColorValue = 0;
/**
 * Display the selector which allows the user to select the color that should be used for drawing the lines for the selected node
 */
function displayColors() {
    var newOptions = {
        '0' : 'White',
        '1' : 'Red',
        '2' : 'Blue',
        '3' : 'Yellow',
        '4' : 'Green'
    };
    var selectedOption = '0';

    var select = $('#colors');
    var options = select.attr('options');
    $('option', select).remove();

    $.each(newOptions, function(val, text) {
        options[options.length] = new Option(text, val);
    });
    select.val(selectedOption);
}

/*
 * Method that handles the drawing/hiding of both coming in and coming out lines.
 * 
 * @param selectedNodeIdx the currently selected node
 * @param direction swap between outgoing(1) and ingoing(0)
 * @param draw swap between drawing(1) or hiding(0)
 */
function handleLines(selectedNodeIdx, direction, draw) {
	if (draw == 1)	{
		setCurrentColorForNode(selectedNodeIdx);
	}
	if (direction == 1) {
		//Coming out lines
		for (var i=0; i<NO_POSITIONS; i++) {
			if (GVAR_interestAreaVariables[GVAR_selectedAreaType]['values'][selectedNodeIdx][i] > 0) {
				GVAR_connectivityMatrix[selectedNodeIdx][i] = draw;				
			}
		}
	} else {
		for (var i=0; i<NO_POSITIONS; i++) {
			if (GVAR_interestAreaVariables[GVAR_selectedAreaType]['values'][i][selectedNodeIdx] > 0) {
				GVAR_connectivityMatrix[i][selectedNodeIdx] = draw;
			}
		}	
	}
 	drawScene();
}

/**
 * Draw all the comming in and comming out lines for the connectivity matrix.
 */
function checkAll() {
	for (var i = 0; i < NO_POSITIONS; i++) {
		var comingInEdgesIndexes = CONN_comingInLinesIndices[i];
		for (var j = 0; j < comingInEdgesIndexes.length; j++) {
			if (GVAR_interestAreaVariables[GVAR_selectedAreaType]['values'][comingInEdgesIndexes[j]][i] > 0 )
             GVAR_connectivityMatrix[comingInEdgesIndexes[j]][i] = 1;
        }
        var comingOutEdgesIndexes = CONN_comingOutLinesIndices[i];
		for (var j = 0; j < comingOutEdgesIndexes.length; j++) {
			if (GVAR_interestAreaVariables[GVAR_selectedAreaType]['values'][i][comingOutEdgesIndexes[j]] > 0 )
             GVAR_connectivityMatrix[i][comingOutEdgesIndexes[j]] = 1;
        }
	}
    drawScene();
}

/**
 * Clear all the comming in and comming out lines for the connectivity matrix.
 */
function clearAll() {
    for (var i = 0; i < GVAR_connectivityMatrix.length; i++) {
        for (var j = 0; j < GVAR_connectivityMatrix[i].length; j++) {
            GVAR_connectivityMatrix[i][j] = 0;
        }
    }
    drawScene();
}


/**
 * Draw all the comming in and comming out lines for the connectivity matrix for selected nodes.
 */
function checkAllSelected() {
	for (var i = 0; i < NO_POSITIONS; i++) {
		if (GFUNC_isNodeAddedToInterestArea(i)) {
			var comingInEdgesIndexes = CONN_comingInLinesIndices[i];
			for (var j = 0; j < comingInEdgesIndexes.length; j++) {
				if (GFUNC_isNodeAddedToInterestArea(j) && GVAR_interestAreaVariables[GVAR_selectedAreaType]['values'][comingInEdgesIndexes[j]][i] > 0)
	             GVAR_connectivityMatrix[comingInEdgesIndexes[j]][i] = 1;
	        }
	        var comingOutEdgesIndexes = CONN_comingOutLinesIndices[i];
			for (var j = 0; j < comingOutEdgesIndexes.length; j++) {
				if (GFUNC_isNodeAddedToInterestArea(j) && GVAR_interestAreaVariables[GVAR_selectedAreaType]['values'][i][comingOutEdgesIndexes[j]] > 0 )
	             GVAR_connectivityMatrix[i][comingOutEdgesIndexes[j]] = 1;
	        }
	  }
	}
    drawScene();
}

/**
 * Clear all the comming in and comming out lines for the connectivity matrix for selected nodes.
 */
function clearAllSelected() {
    for (var i = 0; i < NO_POSITIONS; i++) {
		if (GFUNC_isNodeAddedToInterestArea(i)) {
			var comingInEdgesIndexes = CONN_comingInLinesIndices[i];
			for (var j = 0; j < comingInEdgesIndexes.length; j++) {
				if (GFUNC_isNodeAddedToInterestArea(j) && GVAR_interestAreaVariables[GVAR_selectedAreaType]['values'][comingInEdgesIndexes[j]][i] > 0)
	             GVAR_connectivityMatrix[comingInEdgesIndexes[j]][i] = 0;
	        }
	        var comingOutEdgesIndexes = CONN_comingOutLinesIndices[i];
			for (var j = 0; j < comingOutEdgesIndexes.length; j++) {
				if (GFUNC_isNodeAddedToInterestArea(j) && GVAR_interestAreaVariables[GVAR_selectedAreaType]['values'][i][comingOutEdgesIndexes[j]] > 0 )
	             GVAR_connectivityMatrix[i][comingOutEdgesIndexes[j]] = 0;
	        }
	  }
	}
    drawScene();
    drawScene();
}


/**
 * Change the color that should be used for drawing the lines for the selected node
 *
 * @param selectedNodeIndex the index of the selected node
 */
function setCurrentColorForNode(selectedNodeIndex) {
    colorsIndexes[selectedNodeIndex*3] = getNewNodeColor()[0]/255.0;
    colorsIndexes[selectedNodeIndex*3+1] = getNewNodeColor()[1]/255.0;
    colorsIndexes[selectedNodeIndex*3+2] = getNewNodeColor()[2]/255.0;

    colorsArrayBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, colorsArrayBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(colorsIndexes), gl.STATIC_DRAW);
    colorsArrayBuffer.itemSize = 3;
    colorsArrayBuffer.numItems = parseInt(colorsIndexes.length);
}


var verticesBuffers = [];
var normalsBuffers = [];
var indexesBuffers = [];
var hemispheres = ['leftHemisphere', 'rightLeftQuarter', 'leftRightQuarter', 'rightHemisphere'];
var connectivity_nose_correction;
var GVAR_additionalXTranslationStep = 0;
var GVAR_additionalYTranslationStep = 0;


function applyConnectivityNoseCorrection() {
    if (connectivity_nose_correction != undefined && connectivity_nose_correction != null &&
            connectivity_nose_correction.length == 3) {
        mvRotate(parseInt(connectivity_nose_correction[0]), [1, 0, 0]);
        mvRotate(parseInt(connectivity_nose_correction[1]), [0, 1, 0]);
        mvRotate(parseInt(connectivity_nose_correction[2]), [0, 0, 1]);
    }
}

/**
 * Returns <code>true</code> if at least one point form the given list is checked.
 *
 * @param listOfIndexes the list of indexes for the points that should be verified. Each 2 elements from this list represent a point
 * (the indexes i and j from the connectivityMatrix in which is kept the information about the checked/unchecked points)
 * 
 * dir = 0 -> ingoing
 * dir = 1 -> outgoing
 * 
 * idx -> point in question
 */
function isAnyPointChecked(idx, listOfIndexes, dir) {	
    for (var i = 0; i < listOfIndexes.length; i++) {
        var idx1 = listOfIndexes[i];
		if (dir == 0) {
	        if (GVAR_connectivityMatrix[idx1][idx] == 1 ) {
	            return true;
	        }			
		}
		if (dir == 1) {
	        if (GVAR_connectivityMatrix[idx][idx1] == 1 ) {
	            return true;
	        }			
		}
    }
    return false;
}

function hasPositiveWeights(i) {
    var hasWeights = false;
    for (var j = 0; j < NO_POSITIONS; j++) {
    	if ((GVAR_interestAreaVariables[GVAR_selectedAreaType]['values'][i][j] > 0 || GVAR_interestAreaVariables[GVAR_selectedAreaType]['values'][j][i] > 0) && (i != j)) {
    		hasWeights = true;
    	}
    }
    return hasWeights;
}
/**
 * Create webgl buffers from the specified files
 *
 * @param urlList the list of files urls
 * @param resultBuffers a list in which will be added the buffers created based on the data from the specified files
 */
function getAsynchronousBuffers(urlList, resultBuffers, isIndex) {
    if (urlList.length == 0) {
        noOfBuffersToLoad -= 1;
        return;
    }
    $.get(urlList[0], function(data) {
        var dataList = eval(data);
        var buffer = gl.createBuffer();
        if (isIndex) {
        	gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, buffer);
        	gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, new Uint16Array(dataList), gl.STATIC_DRAW);
        	buffer.numItems = dataList.length;
        } else {
	        gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
	        gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(dataList), gl.STATIC_DRAW);
		}
        resultBuffers.push(buffer);
        urlList.splice(0, 1);
        return getAsynchronousBuffers(urlList, resultBuffers, isIndex);
    });
}


function selectHemisphere(index) {
	$(".quadrant-display").each(function (listItem) {
		$(this).removeClass('active');
	});
	$(".quadrant-"+ index).each(function (listItem) {
		$(this).addClass('active');
	});
	
	for (var k=0; k<hemispheres.length; k++){
		$("#" + hemispheres[k]).hide();
		$("#" + hemispheres[k]+'Tracts').hide();
	}
    $("#" + hemispheres[index]).show();
    $("#" + hemispheres[index]+'Tracts').show();
	var inputDiv = document.getElementById('editNodeValues');
	inputDiv.style.display = 'none';
    highlightPoint();
}


/**
 * Method which draws the cortical surface
 */
function drawHemispheres(drawingMode) {
    gl.uniform1i(shaderProgram.colorIndex, GRAY_COLOR_INDEX);
    for (var i = 0; i < verticesBuffers.length; i++) {
        gl.bindBuffer(gl.ARRAY_BUFFER, verticesBuffers[i]);
        gl.vertexAttribPointer(shaderProgram.vertexPositionAttribute, TRI, gl.FLOAT, false, 0, 0);
        gl.bindBuffer(gl.ARRAY_BUFFER, normalsBuffers[i]);
        gl.vertexAttribPointer(shaderProgram.vertexNormalAttribute, TRI, gl.FLOAT, false, 0, 0);
        //todo-io: hack for colors buffer
        //todo-io: there should be passed an buffer of colors indexes not the verticesBuffers;
        //todo-io: although we pass the color as a uniform we still have to set the aColorIndex attribute
        gl.bindBuffer(gl.ARRAY_BUFFER, verticesBuffers[i]);
        gl.vertexAttribPointer(shaderProgram.colorAttribute, 3, gl.FLOAT, false, 0, 0);
        gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, indexesBuffers[i]);
        setMatrixUniforms();
        gl.drawElements(drawingMode, indexesBuffers[i].numItems, gl.UNSIGNED_SHORT, 0);
    }
}


/**
 * @param isSingleMode if is <code>true</code> that means that the connectivity will
 * be drawn alone, without widths and tracts.
 */
function connectivity_startGL(isSingleMode) {
	/*
	 * Contains GL initializations that need to be done each time the standard connectivity view is 
	 * selected from the available tabs.
	 */
	GL_DEFAULT_Z_POS = -310.0;
	GL_zTranslation = GL_DEFAULT_Z_POS;
		
    for (var i = 0; i < COLORS.length; i++) {
        gl.uniform3f(shaderProgram.colorsArray[i], COLORS[i][0], COLORS[i][1], COLORS[i][2]);
    }
    
    gl.clearColor(0.0, 0.0, 0.0, 1.0);
    gl.clearDepth(1.0);
    gl.enable(gl.DEPTH_TEST);
    gl.depthFunc(gl.LEQUAL);

    if (!isSingleMode) {
        selectHemisphere(0);
    }
    //drawInterestAreaMatrix(pointsLabels, weights);
    GL_initColorPickFrameBuffer();
    drawScene();
}

function connectivity_initCanvas() {
	/*
	 * Initialize the canvas and the event handlers. This should be called when switching from 
	 * other GL based visualizers to re-initiate the canvas.
	 */
	var canvas = document.getElementById(CONNECTIVITY_CANVAS_ID);
    initGL(canvas);
    initShaders();
    // Enable keyboard and mouse interaction
    canvas.onkeydown = customKeyDown;
    canvas.onkeyup = GL_handleKeyUp;
    canvas.onmousedown = customMouseDown;
    document.onmouseup = GL_handleMouseUp;
    document.onmousemove = customMouseMove;
}

function saveRequiredInputs_con(fileWeights, fileTracts, filePositions, urlVerticesList, urlTrianglesList,
								urlNormalsList, conn_nose_correction, alpha_value) {
	/*
	 * Initialize all the actual data needed by the connectivity visualizer. This should be called
	 * only once.
	 */
	GVAR_initPointsAndLabels(filePositions);
    alphaValue = alpha_value;
    connectivity_nose_correction = $.parseJSON(conn_nose_correction);
    NO_POSITIONS = GVAR_positionsPoints.length;
    GFUNC_initTractsAndWeights(fileWeights, fileTracts)

    // Initialize the buffers for drawing the points
    for (i = 0; i < NO_POSITIONS; i++) {
        positionsBuffers[i] = HLPR_bufferAtPoint(gl, GVAR_positionsPoints[i]);
    }
    initBuffers();
    ORIENTATION_initOrientationBuffers();

    var urlVertices = $.parseJSON(urlVerticesList);
	if (urlVertices.length > 0) {
		var urlNormals = $.parseJSON(urlNormalsList);
    	var urlTriangles = $.parseJSON(urlTrianglesList);
	    getAsynchronousBuffers(urlVertices, verticesBuffers);
	    getAsynchronousBuffers(urlNormals, normalsBuffers);
	    getAsynchronousBuffers(urlTriangles, indexesBuffers, true);		
	}
    GFUNC_initConnectivityMatrix(NO_POSITIONS);
    // Initialize the indices buffers for drawing the lines between the drawn points
    initLinesIndices();
}

/**
 * @param isSingleMode if is <code>true</code> that means that the connectivity will
 * be drawn alone, without widths and tracts.
 */
function prepareConnectivity(fileWeights, fileTracts, filePositions, urlVerticesList , urlTrianglesList,
                    urlNormalsList, conn_nose_correction, alpha_value, isSingleMode) {
	/*
	 * This will take all the required steps to start the connectivity visualizer.
	 */
	connectivity_initCanvas();
	saveRequiredInputs_con(fileWeights, fileTracts, filePositions, urlVerticesList , urlTrianglesList,
                    	   urlNormalsList, conn_nose_correction, alpha_value);
	connectivity_startGL(isSingleMode);
    if (!isSingleMode) {
        GFUNC_addAllMatrixToInterestArea();
    }
}

