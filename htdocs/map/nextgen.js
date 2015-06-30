var map;
var vectorLayer;
var iaextent;
var scenario = 0;
var maxvalue = 0;
var MRMS_FLOOR = new Date("2013/08/20");
var myDateFormat = 'M d, yy';
var geojsonFormat = new ol.format.GeoJSON();
var quickFeature;
var detailedFeature;
var featureOverlay;

var levels = [0.001, 0.1, 0.5,  1.,  5., 7.];
var colors = ['rgba(0, 0, 255, 1)',

			  'rgba(0, 212, 255, 1)',

			  'rgba(102, 255, 153, 1)',

			  'rgba(204, 255, 0, 1)',

			  'rgba(255, 232, 0, 1)',

			  'rgba(255, 153, 0, 1)'];

var vardesc = {
	avg_runoff: 'Runoff is the average amount of water that left the hillslopes via above ground transport.',
	avg_loss: 'Soil Detachment is the average amount of soil disturbed on the modelled hillslopes.',
	qc_precip: 'Precipitation is the average amount of rainfall and melted snow received on the hillslopes.',
	avg_delivery: 'Delivery is the average amount of soil transported to the bottom of the modelled hillslopes.',
}

var varunits = {
	avg_runoff: 'inches',
	avg_loss: 'tons per acre',
	qc_precip: 'inches',
	avg_delivery: 'tons per acre'
};
var vartitle = {
	avg_runoff: 'Water Runoff',
	avg_loss: 'Soil Detachment',
	qc_precip: 'Daily Precipitation',
	avg_delivery: 'Soil Delivery'
};

// Sets the date back to today
function setToday(){
	appstate.date = lastdate;
	$('#datepicker').datepicker("setDate", appstate.date);
	remap();
	$('#settoday').css('display', 'none');
}
// Sets the title shown on the page for what is being viewed
function setTitle(){
	dt = $.datepicker.formatDate(myDateFormat, appstate.date);
	dtextra = (appstate.date2 === null) ? '': ' to '+$.datepicker.formatDate(myDateFormat, appstate.date2);
	$('#maptitle').html(vartitle[appstate.ltype] +" ["+
			varunits[appstate.ltype] +"] for "+ dt +" "+ dtextra);
	$('#variable_desc').html(vardesc[appstate.ltype]);
}

// When user clicks the "Get Shapefile" Button
function get_shapefile(){
	dt = $.datepicker.formatDate("yy-mm-dd", appstate.date);
	window.location.href = 'http://mesonet.agron.iastate.edu/cgi-bin/request/idep2.py?dt='+dt;
}

function setType(t){
	$('#'+ t +'_opt').click();
}

function hideDetails(){
	$('#details_hidden').css('display', 'block');
	$('#details_details').css('display', 'none');
	$('#details_loading').css('display', 'none');
}

function updateDetails(huc12){
	$('#details_hidden').css('display', 'none');
	$('#details_details').css('display', 'none');
	$('#details_loading').css('display', 'block');
    $.get('nextgen-details.php', {
    	huc12: huc12,
		date: $.datepicker.formatDate("yy-mm-dd", appstate.date),
		date2: $.datepicker.formatDate("yy-mm-dd", appstate.date2)
		},
		function(data){
			$('#details_details').css('display', 'block');
			$('#details_loading').css('display', 'none');
			$('#details_details').html(data);
	});

}

function get_tms_url(){
	// Generate the TMS URL given the current settings
	var uri = '/geojson/huc12.py?date='+$.datepicker.formatDate("yy-mm-dd", appstate.date);
	if (appstate.date2 !== null){
		uri = uri + "&date2="+ $.datepicker.formatDate("yy-mm-dd", appstate.date2);
		levels = [0.001, 0.5, 1, 5, 10, 20];
	} else{
		levels = [0.001, 0.1, 0.5,  1.,  5., 7.];	
	}
	return uri;
}
function rerender_vectors(){
	//console.log("rerender_vectors() called");
	// Reset max value
	maxvalue = 0;
	vectorLayer.changed();
}
function remap(){
	// Reset max value
	maxvalue = 0;
	// console.log("remap() called"+ detailedFeature);
	var newsource = new ol.source.Vector({
		url: get_tms_url(),
		format: geojsonFormat
	});
	// We should replace the detailed feature with new information, so that
	// the mouseover does not encounter this old information
	newsource.on('change', function(){
		if (detailedFeature){
			featureOverlay.removeFeature(detailedFeature);
			detailedFeature = vectorLayer.getSource().getFeatureById(detailedFeature.getId());
			featureOverlay.addFeature(detailedFeature);
		}
		drawColorbar();
	});
	vectorLayer.setSource(newsource);
	setTitle();
	if (detailedFeature){
		updateDetails(detailedFeature.getId());
	}
}
function setDate(year, month, date){
	appstate.date = new Date(year+"/"+ month +"/"+ date);
	$('#datepicker').datepicker("setDate", appstate.date);
	remap();
}
function zoom_iowa(){
    map.zoomToExtent(iaextent);
}

function make_iem_tms(title, layername, visible){
	return new ol.layer.Tile({
		title : title,
		visible: visible,
		source : new ol.source.XYZ({
			url : tilecache +'/c/tile.py/1.0.0/'+layername+'/{z}/{x}/{y}.png'
		})
	})
}
function setHUC12(huc12){
	feature = vectorLayer.getSource().getFeatureById(huc12);
	makeDetailedFeature(feature);
	jQuery.noConflict();
	$('#myModal').modal('hide');
}

function makeDetailedFeature(feature){
	if (feature != detailedFeature){
		if (detailedFeature){
			detailedFeature.set('clicked', false);
			featureOverlay.removeFeature(detailedFeature);
		}
		if (feature){
			featureOverlay.addFeature(feature);
		}
		detailedFeature = feature;
	}
	updateDetails(feature.getId());
}

function doHUC12Search(){
	$('#huc12searchres').html('<p><img src="/images/wait24trans.gif" /> Searching...</p>');
	var txt = $('#huc12searchtext').val();
	$.ajax({
		method: 'GET',
		url: '/geojson/hsearch.py',
		data: {q: txt}
	}).done(function(res){
		var tbl = "<table class='table table-striped'><thead><tr><th>ID</th><th>Name</th></tr></thead>";
		$.each(res.results, function(idx, result){
			tbl += "<tr><td><a href=\"javascript: setHUC12('"+ result.huc_12 +"');\">"+ result.huc_12 +"</a></td><td>"+ result.name +"</td></tr>";
		});
		tbl += "</table>";
		$('#huc12searchres').html(tbl);
	}).fail(function(res){
		$('#huc12searchres').html("<p>Search failed, sorry</p>");
	});
}

function drawColorbar(){
	//console.log("drawColorbar called...");
    var canvas = document.getElementById('colorbar');
    var ctx = canvas.getContext('2d');
    
    canvas.height = colors.length * 20 + 50;
    
    // Clear out the canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    ctx.font = 'bold 12pt Calibri';
    ctx.fillStyle = 'white';
    var metrics = ctx.measureText('Legend');
    ctx.fillText('Legend', (canvas.width / 2) - (metrics.width / 2), 14);

    var txt = "Max: "+ maxvalue.toFixed(2);
    ctx.font = 'bold 10pt Calibri';
    ctx.fillStyle = 'yellow';
    metrics = ctx.measureText(txt);
    ctx.fillText(txt, (canvas.width / 2) - (metrics.width / 2), 32);

    
    var pos = 20;
    $.each(colors, function(idx, c){
        ctx.beginPath();
        ctx.rect(5, canvas.height - pos - 10, 20, 20);
        ctx.fillStyle = c;
        ctx.fill();

        ctx.font = 'bold 12pt Calibri';
        ctx.fillStyle = 'white';
        metrics = ctx.measureText(levels[idx]);
        ctx.fillText(levels[idx], 45 - (metrics.width/2), canvas.height - (pos-20) -4);

        pos = pos + 20;
    });

}


$(document).ready(function(){

	appstate.date = lastdate;
	appstate.date2 = null;

	var style = new ol.style.Style({
		  fill: new ol.style.Fill({
		    color: 'rgba(255, 255, 255, 0)'
		  }),
		  stroke: new ol.style.Stroke({
		    color: '#319FD3',
		    width: 1
		  })
		});

	vectorLayer = new ol.layer.Vector({
		title : 'IDEPv2 Data Layer',
		  source: new ol.source.Vector({
			  url: get_tms_url(),
			  format: geojsonFormat
		  }),
		  style: function(feature, resolution) {
			  val = feature.get(appstate.ltype);
			  if (val > maxvalue){
				  //console.log("Setting maxvalue to "+ val);
				  maxvalue = val;
				  drawColorbar();
			  }
			  var c = 'rgba(255, 255, 255, 0)';
			  for (var i=levels.length; i>=0; i--){
			      if (val >= levels[i]){
			    	 c = colors[i];
			    	 break;
			      }
			      
			  }
			  style.getFill().setColor(c); 
		    // style.getText().setText(resolution < 5000 ? feature.get('avg_loss') : '');
		    return [style];
		  }
		});
	
	// Create map instance
    map = new ol.Map({
        target: 'map',
        controls: [new ol.control.Zoom(),
            new ol.control.ZoomToExtent({
            	//map.getView().calculateExtent(map.getSize())
            	extent: [-10889524, 4833877, -9972280, 5488178]
            })
        ],
        layers: [new ol.layer.Tile({
            	title: 'OpenStreetMap',
            	visible: true,
        		source: new ol.source.OSM()
        	}),
        	new ol.layer.Tile({
                title: "Global Imagery",
                visible: false,
                source: new ol.source.TileWMS({
                        url: 'http://maps.opengeo.org/geowebcache/service/wms',
                        params: {LAYERS: 'bluemarble', VERSION: '1.1.1'}
                })
        	}),
        	make_iem_tms('Iowa 100m Hillshade', 'iahshd-900913', false),
        	vectorLayer,
        	make_iem_tms('Iowa Counties', 'iac-900913', false),
        	make_iem_tms('US States', 's-900913', true),
        	make_iem_tms('Hydrology', 'iahydrology-900913', false),
        	make_iem_tms('HUC 8', 'iahuc8-900913', false)
        ],
        view: new ol.View({
                projection: 'EPSG:3857',
                center: ol.proj.transform([-93.5, 42.1], 'EPSG:4326', 'EPSG:3857'),
                zoom: 7
        })
    });

    var highlightStyle = [new ol.style.Style({
            stroke: new ol.style.Stroke({
              color: '#f00',
              width: 1
            }),
            fill: new ol.style.Fill({
              color: 'rgba(255,0,0,0.1)'
            })
    })];
    var clickStyle = [new ol.style.Style({
        stroke: new ol.style.Stroke({
            color: '#000',
            width: 2
          })
    })];

    featureOverlay = new ol.FeatureOverlay({
      map: map,
      style: function(feature, resolution) {
    	// console.log('processing style for '+ feature.getId());
        if (detailedFeature && feature.getId() == detailedFeature.getId()){
        	return clickStyle;
        }
        return highlightStyle;
      }
    });


    var displayFeatureInfo = function(pixel) {

      var feature = map.forEachFeatureAtPixel(pixel, function(feature, layer) {
        return feature;
      });

      var info = document.getElementById('info');
      if (feature) {
    	  $('#info-huc12').html( feature.getId() );
    	  $('#info-loss').html( feature.get('avg_loss').toFixed(3) + " T/a" );
    	  $('#info-runoff').html( feature.get('avg_runoff').toFixed(2) + " in" );
    	  $('#info-delivery').html( feature.get('avg_delivery').toFixed(3) + " T/a" );
    	  $('#info-precip').html( feature.get('qc_precip').toFixed(2) + " in");
      } else {
          $('#info-huc12').html('&nbsp;');
          $('#info-loss').html('&nbsp;');
          $('#info-runoff').html('&nbsp;');
          $('#info-delivery').html('&nbsp;');
          $('#info-precip').html('&nbsp;');
      }

      // Keep only one selected
      if (feature !== quickFeature) {
        if (quickFeature) {
          featureOverlay.removeFeature(quickFeature);
        }
        if (feature) {
          featureOverlay.addFeature(feature);
        }
        quickFeature = feature;
      }

    };

    // fired as the pointer is moved over the map
    map.on('pointermove', function(evt) {
      if (evt.dragging) {
        return;
      }
      var pixel = map.getEventPixel(evt.originalEvent);
      displayFeatureInfo(pixel);
    });

    // fired as somebody clicks on the map
    map.on('click', function(evt) {
    	// console.log('map click() called');
    	var pixel = map.getEventPixel(evt.originalEvent);
    	var feature = map.forEachFeatureAtPixel(pixel, function(feature, layer) {
            return feature;
        });
    	if (feature){
        	makeDetailedFeature(feature);
    	} else {
    		alert("No features found for where you clicked on the map.");
    	}
    });
    
    // Create a LayerSwitcher instance and add it to the map
    var layerSwitcher = new ol.control.LayerSwitcher();
    map.addControl(layerSwitcher);
    
    $("#datepicker").datepicker({
  	  dateFormat: myDateFormat,
  	  minDate: new Date(2007, 1, 1),
  	  maxDate: lastdate,
  	   onSelect: function(dateText, inst) {
  		   appstate.date = $("#datepicker").datepicker("getDate");
  		   remap();
  		   if (appstate.date != lastdate){
  			 $('#settoday').css('display', 'block');
  		   }
  	   }
    });

    $("#datepicker").datepicker('setDate', lastdate);

    $("#datepicker2").datepicker({
    	disable: true,
    	  dateFormat: myDateFormat,
    	  minDate: new Date(2007, 1, 1),
    	  maxDate: lastdate,
    	   onSelect: function(dateText, inst) {
    		   appstate.date2 = $("#datepicker2").datepicker("getDate");
    		   remap(); 
    	   }
      });

      $("#datepicker2").datepicker('setDate', lastdate);
    
    $("#radio").buttonset();
    $( '#radio input[type=radio]').change(function(){
  	  	appstate.ltype = this.value;
    	rerender_vectors();
    	setTitle();
    });
    $("#t").buttonset();
    $( '#t input[type=radio]').change(function(){
    	if (this.value == 'single'){
    		appstate.date2 = null;
        	$("#dp2").css('visibility', 'hidden');    		
    		
    	} else {
    		appstate.date2 = $("#datepicker2").datepicker("getDate");
        	$("#dp2").css('visibility', 'visible');
    		remap();
    	}
    });
    $('#huc12searchtext').on('keypress', function (event) {
        if(event.which === 13){
        	doHUC12Search();
        }
    });
        
        
    $('#huc12searchbtn').on('click', function(){
    	doHUC12Search();
    	
    });
    
    setTitle();
    // Make the map 6x4
    sz = map.getSize();
    map.setSize([sz[0], sz[0] / 6. * 4.]);
    drawColorbar();
}); // End of document.ready()
