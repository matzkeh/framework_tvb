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

/*
 * ---------------------------------------===========================================--------------------------------------
 * WARNING: This script is just adding some functionality specific to the stimulus visualization on top of what is defined 
 * in /static/js/vertice_pick/base_vertice_pick.js. As such in all the cases when this script is used, you must first 
 * include base_vertice_pick.js. In case you need to ADD FUNCTIONS here, either make sure you don't "overwrite" something
 * necessary from base_vertice_pick.js, or just prefix your functions. (e.g. STIM_PICK_${function_name}).
 * ---------------------------------------===========================================--------------------------------------
 */
var BUFFER_TIME_STEPS = 8;
var DATA_CHUNK_SIZE = null;
var triangles_list = null;
var colorBuffers = [];
var TICK_STEP = 200;
var maxValue = 0;
var minValue = 0;
var startColor = [0.5, 0.5, 0.5]
var endColor = [1, 0, 0]
var drawTickInterval = null;
var sliderSel = false;
var minTime = 0;
var maxTIme = 0;
var displayedStep = 0;
var totalTimeStep = 0;
var currentStimulusData = null;
var nextStimulusData = null;
var asyncLoadStarted = false;
var endReached = false;

function STIM_PICK_setVisualizedData(data) {
	/*
	 * Start the movie mode visualization of the recieved data.
	 */
	BASE_PICK_isMovieMode = true;
	currentStimulusData = data['data'];
	minTime = data['time_min']
	maxTime = data['time_max']
	DATA_CHUNK_SIZE = data['chunk_size']
	maxValue = data['max']
	/*
	 * If for some reason the draw timeout was not cleared, clear it now.
	 */
	if (drawTickInterval != null) {
		clearInterval(drawTickInterval);
	}
	endReached = false;
	/*
	 * Reset the flags and set a new draw timeout.
	 */
	drawTickInterval = setInterval(tick, TICK_STEP);
	displayedStep = 0;
	totalTimeStep = minTime;
	STIM_PICK_initLegendInfo();
	/*
	 * Create the slider to display the total time.
	 */
	var sliderDiv = document.createElement('DIV');
	sliderDiv.className = "shadow";
	sliderDiv.id = "slider";
	document.getElementById("slider-div").appendChild(sliderDiv);
	
	$("#slider").slider({ min:minTime, max: maxTime, disabled: true,
	            slide: function(event, ui) {
	            	sliderSel = true;
	                totalTimeStep = $("#slider").slider("option", "value");
	                displayedStep = parseInt((totalTimeStep - minTime) % DATA_CHUNK_SIZE);
	            },
	            stop: function(event, ui) {
	            	sliderSel = false;
	            } });
}

function STIM_PICK_initLegendInfo() {
	/*
	 * Init the legend information for this stimulus.
	 */
	document.getElementById('brainLegendDiv').innerHTML = '';
	LEG_initMinMax(0, maxValue);
	if (maxValue == 0) { maxValue = 1; }
	var legendStep = maxValue / 6;
	var legendValues = [];
	for (var i = 0; i < maxValue; i = i + legendStep) {
		legendValues.push(i);
	}
	var tableElem = document.createElement('TABLE');
	tableElem.style.height = '100%';
	
	var tableRow = document.createElement('TR');
	tableRow.style.height = '20px';
	var tableData = document.createElement('TD');
	tableData.innerHTML = '<label>' + legendValues[legendValues.length-1].toFixed(4) + '</label>';
	tableRow.appendChild(tableData);
	tableElem.appendChild(tableRow);

	for (var i = (legendValues.length - 2); i >= 0; i--) {
		var tableRow = document.createElement('TR');
		tableRow.style.height = 100 / legendValues.length + '%';
		tableRow.style.verticalAlign = 'bottom';
		var tableData = document.createElement('TD');
		tableData.innerHTML = '<label>' + legendValues[i].toFixed(4) + '</label>';
		tableRow.appendChild(tableData);
		tableElem.appendChild(tableRow);
	}
	document.getElementById('brainLegendDiv').appendChild(tableElem);
}

function STIM_PICK_stopDataVisualization() {
	/*
	 * Stop the movie-mode visualization. Reset flags and steps, also remove the
	 * tick - timeout and reset the color buffers.
	 */
    if (noOfUnloadedBrainDisplayBuffers != 0) {
        displayMessage("The load operation for the surface data is not completed yet!", "infoMessage");
        return;
    }
	BASE_PICK_isMovieMode = false;
	document.getElementById('brainLegendDiv').innerHTML = '';
	displayedStep = 0;
	if (drawTickInterval != null) {
		clearInterval(drawTickInterval);
	}
	document.getElementById("slider-div").innerHTML = '';
	document.getElementById("TimeNow").innerHTML = '';
	asyncLoadStarted = false;
	for (var i=0; i<BASE_PICK_brainDisplayBuffers.length; i++) {
		var fakeColorBuffer = gl.createBuffer();
	    gl.bindBuffer(gl.ARRAY_BUFFER, fakeColorBuffer);
	    var thisBufferColors = new Float32Array(BASE_PICK_brainDisplayBuffers[i][0].numItems/ 3 * 4);
	    for (var j = 0; j < BASE_PICK_brainDisplayBuffers[i][0].numItems / 3 * 4; j++) {
	    	thisBufferColors[j] = 0.5;
	    }
	    gl.bufferData(gl.ARRAY_BUFFER, thisBufferColors, gl.STATIC_DRAW);
	    BASE_PICK_brainDisplayBuffers[i][3] = fakeColorBuffer;
	}
    drawScene();
}


function STIM_PICK_loadNextStimulusChunk() {
	/*
	 * Since the min-max interval can be quite large, just load it in chunks.
	 */
	var currentChunkIdx = parseInt((totalTimeStep - minTime) / DATA_CHUNK_SIZE);
	if ((currentChunkIdx + 1) * DATA_CHUNK_SIZE < (maxTime - minTime)) {
		/*
		 * We haven't reached the final chunk so just load it normally.
		 */
		asyncLoadStarted = true;
		$.ajax({
			        type:'GET',
			        url:'/spatial/stimulus/surface/get_stimulus_chunk/' + (currentChunkIdx + 1),
			        success:function (data) {
			            nextStimulusData = $.parseJSON(data);
			            asyncLoadStarted = false;
			        }
			    });
	} else {
		/*
		 * No more chunks to load. Set end of data flat and block the async load by setting
		 * asyncLoadStarted to true so no more calls to loadNextStimulusChunk are done for
		 * this data.
		 */
		asyncLoadStarted = true;
		endReached = true;
	}
}

function tick() {
	/*
	 * Function called every TICK_STEP milliseconds. This is only done in movie mode.
	 */
    if (noOfUnloadedBrainDisplayBuffers != 0) {
        displayMessage("The load operation for the surface data is not completed yet!", "infoMessage");
        return;
    }
	if (sliderSel == false) {
		//If we reached maxTime, the movie ended
		if (BASE_PICK_isMovieMode == true && totalTimeStep < maxTime) {
			/*
			 * We are still in movie mode and didn't pass the end of the data.
			 */
		    if (displayedStep >= currentStimulusData.length) {
		    	if (currentStimulusData.length > maxTime - minTime || endReached == true) {
		    		//We had reached the end of the movie mode.
		    		STIM_PICK_stopDataVisualization();
					$('.action-run')[0].className = $('.action-run')[0].className.replace('action-idle', '');
					$('.action-stop')[0].className = $('.action-stop')[0].className + " action-idle";
		    	} else {
		    		//If the async load of the next data chunk is done, do the switch
		    		//otherwise just wait
		    		if (nextStimulusData != null) {
		    			currentStimulusData = nextStimulusData;
		    			displayedStep = 0;
		    			nextStimulusData = null;
		    		} else {
		    			return;
		    		}
		    	}
		    }
			var thisStepData = currentStimulusData[displayedStep];
			/*
			 * Compute the colors for this current step.
			 */
			var diffColor = [endColor[0] - startColor[0],
							 endColor[1] - startColor[1],
							 endColor[2] - startColor[2]]
			
			for (var i=0; i<BASE_PICK_brainDisplayBuffers.length;i++) {
				BASE_PICK_brainDisplayBuffers[i][3] = null;
				var upperBoarder = BASE_PICK_brainDisplayBuffers[i][0].numItems / 3;
			    var thisBufferColors = new Float32Array(upperBoarder * 4);
			    var offset_start = i * 40000;
			    for (var j = 0; j < upperBoarder; j++) {
			    	if (maxValue == minValue) {
			    		var colorDiff = 0;
			    	} else {
			    		var colorDiff = (thisStepData[offset_start + j] - minValue) / maxValue;
			    	}
			        var sub_f32s = thisBufferColors.subarray(j * 4, (j + 1) * 4);
			        sub_f32s[0] = startColor[0] + colorDiff * diffColor[0];
			        sub_f32s[1] = startColor[1] + colorDiff * diffColor[1];
			        sub_f32s[2] = startColor[2] + colorDiff * diffColor[2];
			        sub_f32s[3] = 1;
			    }
		    	BASE_PICK_brainDisplayBuffers[i][3] = gl.createBuffer();
		    	gl.bindBuffer(gl.ARRAY_BUFFER, BASE_PICK_brainDisplayBuffers[i][3]);
	            gl.bufferData(gl.ARRAY_BUFFER, thisBufferColors, gl.STATIC_DRAW);
	            thisBufferColors = null;
			}
			//Redraw the scene 
		    drawScene();
		} else {
			//We had reached the end of the movie mode.
    		STIM_PICK_stopDataVisualization();
			$('.action-run')[0].className = $('.action-run')[0].className.replace('action-idle', '');
			$('.action-stop')[0].className = $('.action-stop')[0].className + " action-idle";
		}
	}
}


function drawScene() {
	if (GL_zoomSpeed != 0) {
		/*
		 * Handle the zoom event before drawing the brain.
		 */
        GL_zTranslation -= GL_zoomSpeed * GL_zTranslation;
        GL_zoomSpeed = 0;
    }
    /*
     * Use function offered by base_vertice_pick.js to draw the brain.
     */
	BASE_PICK_drawBrain(BASE_PICK_brainDisplayBuffers, noOfUnloadedBrainDisplayBuffers);
	if (BASE_PICK_isMovieMode == true) {
		/*
		 * We are in movie mode so drawScene was called automatically. We don't 
		 * want to update the slices here to improve performance. Increse the timestep.
		 */
		displayedStep = displayedStep + 1;
		totalTimeStep = totalTimeStep + 1;
		if (currentStimulusData.length < (maxTime - minTime) && displayedStep + BUFFER_TIME_STEPS >= currentStimulusData.length && nextStimulusData == null && asyncLoadStarted == false) {
			STIM_PICK_loadNextStimulusChunk();
		}
		if (sliderSel == false) {
				document.getElementById("TimeNow").innerHTML = "Time: " + totalTimeStep + " ms";
		        $("#slider").slider("option", "value", totalTimeStep);
		    }
		/*
		 * Draw the legend for the stimulus now.
		 */
		loadIdentity();
	    addLight();
		drawBuffers(gl.TRIANGLES, [LEG_legendBuffers], false);
	} else {
		/*
		 * We are not in movie mode. The drawScene was called from some ui event (e.g. 
		 * 	mouse over). Here we can afford to update the 2D slices because performance is
		 * not that much of an issue.
		 */
		BASE_PICK_drawSlices();
		BASE_PICK_drawBrain(BASE_PICK_brainDisplayBuffers, noOfUnloadedBrainDisplayBuffers);
	}
}