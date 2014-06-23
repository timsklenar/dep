<?php 
require_once "../../config/settings.inc.php";
?>
<html>
<head>
 <link type="text/css" href="/css/ui-lightness/jquery-ui-1.8.22.custom.css" rel="stylesheet" />
 <script type="text/javascript" src="/js/jquery-1.7.2.min.js"></script>
 <script type="text/javascript" src="/js/jquery-ui-1.8.22.custom.min.js"></script>
 <script src="http://maps.google.com/maps/api/js?v=3&amp;sensor=false"></script>
 <script src='/js/OpenLayers.js'></script>
 <link rel='stylesheet' 
  href='/css/default/style.css' type='text/css'>
          <style type="text/css">
     .dp {
     border: 0px;
background: black;
color: white;
font-weight: bolder;
font-size: 1.3em;
width: 149px;
float: left;
     }
            html, body, #map {
                margin: 0;
                width: 100%;
                height: 100%;
            }
            #detailsContainer {
                position: absolute;
                bottom: 1em;
                right: 1em;
                width: 240px;
                z-index: 20001;
                background-color: #53675A;
                padding: 0.1em;
            }
            #details {
                background-color: #FFF;
                padding: 0.1em;
            }
            #controller {
                position: absolute;
                bottom: 0.5em;
                left: 0.5em;
                padding-right: 0.5em;
                background-color: #000;
                z-index: 20001;
                padding-left: 0.5em;
            }
            #ramp {
                position: absolute;
                bottom: 50px;
                left: 0.5em;
                background-color: #000;
                z-index: 20000;
                padding-left: 0.5em;
            }
			#quick {
				position: absolute;
				top: 0px;
				left: 50px;
				z-index: 20000;
			}
			#quick ul {
				float: right;
				list-style-type: none;
				padding: 0;
				margin: 0;
				margin-right: -2px;
			}
			#quick li {
				float: left;
				margin: 0;
				border: 1px solid #999;
				padding: 6px 8px 3px 8px;
				margin-left: -1px;
				background: white;
			}
        </style>
        <script type="text/javascript">
var tilecache = "<?php echo TMS_SERVER; ?>";
        </script>
 <script src='nextgen.js?v=4'></script>
</head>
<body onload="init()">
<div id="quick">
<ul>
	<li><a href="javascript: selectEvent(1);">May6, 07</a></li>
	<li><a href="javascript: selectEvent(2);">Jun4, 08</a></li>
	<li><a href="javascript: selectEvent(3);">Jul24, 08</a></li>
	<li><a href="javascript: selectEvent(4);">Aug24, 07</a></li>
	<li><a href="javascript: selectEvent(5);">Jul22, 10</a></li>
</ul>
</div>
<div id="detailsContainer">
	<div id="details">
		<div id="details_loading"><img src="/images/wait24trans.gif" /> Loading...</div>
		<div id="details_details"></div>
		<div id="details_hidden">Move icon on map to load again</div>
	</div>
</div>
<div id="controller">
	<form>
	<input type="text" name="date" id="datepicker" class="dp" />
	<span style="font-size: 1.3em; color:#FFF; font-weight:bolder;">Iowa Daily Erosion Project</span>
	<input type="button" onclick="javascript: tms.setOpacity(tms.opacity - 0.1);" value="-"/>
	<input type="button" onclick="javascript: tms.setOpacity(tms.opacity + 0.1);" value="+"/>
	<input type="button" onclick="javascript: zoom_iowa();" value="View Iowa"/>
	
	<br clear="both"/>&nbsp;<br />
	<div id="radio">
		<input type="radio" id="precip-in2_opt" name="radio" value="mrms-calday" /><label for="precip-in2_opt">Precipitation</label>
		<input type="radio" id="precip-in_opt" name="radio" value="precip-in" /><label for="precip-in_opt">P.v1</label>
	    <input type="radio" id="loss2_opt" name="radio" value="loss2" checked="checked" /><label for="loss2_opt">Erosion</label>
		<input type="radio" id="loss_opt" name="radio" value="loss" /><label for="loss_opt">E.v1</label>
		<input type="radio" id="runoff2_opt" name="radio" value="runoff2" /><label for="runoff2_opt">Runoff</label>
		<input type="radio" id="runoff_opt" name="radio" value="runoff" /><label for="runoff_opt">R.v1</label>
		<!--  <input type="radio" id="vsm_opt" name="radio" value="vsm2" /><label for="vsm_opt">Root Zone Soil Moisture</label>
		<input type="radio" id="sm10_opt" name="radio" value="sm102" /><label for="sm10_opt">0-4in Soil Moisture</label> 
		-->
	</div>
	</form>
</div>
<div id="ramp">
<img src="/images/loss2-ramp.png" id="rampimg" />
<br /> &nbsp; 
<br /> &nbsp; 
<br /> &nbsp; 
<br /> &nbsp; 
</div>
<div id="map"></div>
</body>
</html>