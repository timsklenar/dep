<?php 
require_once "../../config/settings.inc.php";
require_once "../../include/myview.php";
$dbconn = pg_connect("dbname=idep host=iemdb user=nobody");
$rs = pg_query($dbconn, "SELECT value from properties where key = 'last_date_0'");
$row = pg_fetch_assoc($rs, 0);
$last_date = $row['value'];

$lat = 42.22;
$lon = -95.489;
$OL = "4.3.1";
if (isset($_GET["huc_12"])){
	$huc12 = substr($_GET["huc_12"],0,12);
	$rs = pg_query($dbconn, "with d as "
		."(select ST_transform(st_centroid(geom),4326) as g from huc12 "
		."where huc_12 = '$huc12' and scenario = 0) "
		."select st_x(d.g), st_y(d.g) from d");
	if (pg_num_rows($rs) == 1){
		$row = pg_fetch_assoc($rs,0);
		$lat = $row["st_y"];
		$lon = $row["st_x"];
	}
}


$TMS_SERVER = TMS_SERVER;
$ddd = str_replace("-","/", $last_date);

echo <<<EOM
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DEP :: Map Interface</title>
    <meta name="description" content="Iowa State University, Daily Erosion Project">
    <meta name="author" content="daryl herzmann akrherz@iastate.edu">

	<link href="/vendor/fa/4.7.0/css/font-awesome.min.css" rel="stylesheet">
    <link type="text/css" href="/vendor/openlayers/{$OL}/ol.css" rel="stylesheet" />
    <!-- Le styles -->
    <link type="text/css" href="/vendor/jquery-ui/1.11.4/jquery-ui.min.css" rel="stylesheet" />
    <link href="/vendor/bootstrap/3.3.7/css/bootstrap.min.css" rel="stylesheet">
    <link href="/vendor/jquery-ui/1.11.4/jquery-ui.min.css" rel="stylesheet">
    <!-- IE10 viewport hack for Surface/desktop Windows 8 bug -->
    <link href="/vendor/bootstrap/3.3.7/css/ie10-viewport-bug-workaround.css" rel="stylesheet">

    <!-- Custom styles for app -->
    <link href="nextgen.css" rel="stylesheet">

    <!-- Le HTML5 shim, for IE6-8 support of HTML5 elements -->
    <!--[if lt IE 9]>
      <script src="/js/html5shiv.js"></script>
      <script src="/js/respond.min.js"></script>
    <![endif]-->
    <meta name="twitter:card" content="summary">
	<meta name="twitter:image:src" content="https://mesonet.agron.iastate.edu/images/logo_small.png">
	<meta name="twitter:title" content="DEP :: Map Interface">
	<meta name="twitter:description" content="Daily Erosion Project of Iowa State University">
	<meta name="twitter:url" content="https://dailyerosion.org">
	<meta name="twitter:creator" content="@akrherz">
	<meta name="twitter:image:width" content="85">
	<meta name="twitter:image:height" content="65">

    <!-- Le fav and touch icons -->
    <link rel="shortcut icon" href="/favicon.ico">
    <link rel="apple-touch-icon-precomposed" sizes="144x144" href="/apple-touch-icon-precomposed.png">
    <link rel="apple-touch-icon-precomposed" sizes="114x114" href="/apple-touch-icon-precomposed.png">
    <link rel="apple-touch-icon-precomposed" sizes="72x72" href="/apple-touch-icon-precomposed.png">
    <link rel="apple-touch-icon-precomposed" href="/apple-touch-icon-precomposed.png">

  </head>

  <body>
  <!-- Modals -->
<div id="newdate-message" title="Updated data available" style="display: none;">
  <p>
    <span class="ui-icon ui-icon-circle-check" style="float:left; margin:0 7px 50px 0;"></span>
    The realtime processing has finished and new data is available for date:
	<span id="newdate-thedate"></span>.
  </p>
</div>

<div class="modal fade" id="eventsModal" tabindex="-1" role="dialog" aria-labelledby="eventsModalLabel" aria-hidden="true">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
        <h4 class="modal-title" id="eventsModalLabel">Listing of Daily Events</h4>
      </div>
      <div class="modal-body" onkeypress="return event.keyCode != 13;">
		<div id="eventsres"></div>
		
	  </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
      </div>
    </div>
  </div>
</div>
		
		
<div class="modal fade" id="myModal" tabindex="-1" role="dialog" aria-labelledby="myModalLabel" aria-hidden="true">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
        <h4 class="modal-title" id="myModalLabel">Search for Watershed by Name</h4>
      </div>
      <div class="modal-body" onkeypress="return event.keyCode != 13;">
		<p>Enter some case-insensitive text to search for a watershed by name.</p>
      <form name="huc12search">
		<input type="text" name="q" id="huc12searchtext">
		<button type="button" class="btn btn-default" id="huc12searchbtn">
  <i class="fa fa-search"></i>
</button>
		</form>
		<hr />
		<div id="huc12searchres"></div>
		
	  </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
      </div>
    </div>
  </div>
</div>
  <!-- End of modals -->
  
<div class="container-fluid">
 <div class="row row-offcanvas row-offcanvas-right fill">
  <div class="col-xs-12 fill">
    <div id="map" style="width: 100%; height: 100%; position:fixed;"></div>
	<canvas id="colorbar" width="100" height="100"></canvas>
   </div>
   <div class="col-xs-6 col-sm-3 sidebar-offcanvas" id="sidebar">
     <div class="pull-left">
        <button style="margin-top: 30px;" data-target="q1" class="btn btn-sq-sm btn-danger">
              <i class="fa fa-map"></i></button><br />
        <button data-target="q2" class="btn btn-sq-sm btn-danger">
              <i class="fa fa-wrench"></i></button><br />
        <button data-target="q3" class="btn btn-sq-sm btn-danger">
              <i class="fa fa-info-circle"></i></button><br />
        <button data-target="q4" class="btn btn-sq-sm btn-danger">
              <i class="fa fa-bars"></i></button><br />
        <button style="margin-top: 30px;" class="btn btn-sq-sm btn-danger" id="mapplus">
              <i class="fa fa-search-plus"></i></button><br />
        <button class="btn btn-sq-sm btn-danger" id="mapminus">
              <i class="fa fa-search-minus"></i></button><br />
     </div><!-- ./pull-left buttons -->
    

    <div class="pull-right" id="sidebar-content">
      <div class="pull-right">
    	<button id="close_sidebar" class="btn btn-default" type="button"><i class="fa fa-close"></i></button>
 	  </div>
 	  <div class="clearfix"></div>
 
    <div id="q1">
    	<button id="ia" class="btn btn-default" type="button"><i class="fa fa-search-plus"></i> Iowa</button>
		<button id="ks" class="btn btn-default" type="button"><i class="fa fa-search-plus"></i> Kansas</button>
		<button id="mn" class="btn btn-default" type="button"><i class="fa fa-search-plus"></i> Minnesota</button>
		<button id="ne" class="btn btn-default" type="button"><i class="fa fa-search-plus"></i> Nebraska</button>
		<br clear="all" />
		<strong>Status:</strong> <span id="status">Idle</span>
    	
    	<div id="units_radio">
		  <input type="radio" id="english_opt" name="units" value="0" checked="checked"><label for="english_opt">English</label>
		  <input type="radio" id="metric_opt" name="units" value="1"><label for="metric_opt">Metric</label>
		</div>

		<div id="radio">
		  <input type="radio" id="precip-in2_opt" name="whichlayer" value="qc_precip" checked="checked"><label for="precip-in2_opt">Precipitation</label>
		  <br /><input type="radio" id="runoff2_opt" name="whichlayer" value="avg_runoff"><label for="runoff2_opt">Runoff</label>
		  <br /><input type="radio" id="loss2_opt" name="whichlayer" value="avg_loss"><label for="loss2_opt">Detachment</label>
		  <br /><input type="radio" id="delivery2_opt" name="whichlayer" value="avg_delivery"><label for="delivery2_opt">Hillslope Soil Loss</label>
		</div>
    	
    	<div id="variable_desc"></div>
    
    </div><!-- ./q1 -->
    <div id="q2">
    	<h4>Days to Display</h4>
			<div id="t">
			<input type="radio" id="single" name="t" value="single" checked="checked"><label for="single">Single</label>
			<input type="radio" id="multi" name="t" value="multi"><label for="multi">Multi</label>
			</div>
    
    	<h4>Date:</h4>
			<div class="input-group">
			<span class="input-group-btn"><button id="minus1d" class="btn btn-default" type="button"><i class="fa fa-arrow-left"></i></button></span>
			<input type="text" name="date" id="datepicker" class="form-control" style="font-weight: bolder;">
			<span class="input-group-btn"><button id="plus1d" class="btn btn-default" type="button"><i class="fa fa-arrow-right"></i></button></span>
			</div>

		<div style="display: none;" id="settoday"><a class="btn btn-default" role="button" href="javascript: setToday();"><i class="fa fa-chevron-left"></i> Back to Latest Date</a>
		</div>

		<div style="visibility: hidden;" id="dp2">
			<h4>To Date:</h4>
			<div class="input-group">
			  <input type="text" name="date2" id="datepicker2" class="form-control" style="font-weight: bolder;" />
			</div>
		</div>
		<h4>Tools</h4>
		<div>
		 <button type="button" class="btn btn-default" data-toggle="modal" data-target="#myModal"><i class="fa fa-search"></i> Search</button>
		 <button onclick="javascript: vectorLayer.setOpacity(vectorLayer.getOpacity() - 0.1);" class="btn btn-default" type="button"><i class="fa fa-minus"></i> Decrease Opacity</button>
		 <button onclick="javascript: vectorLayer.setOpacity(vectorLayer.getOpacity() + 0.1);" class="btn btn-default" type="button"><i class="fa fa-plus"></i> Increase Opacity</button>
		 <button onclick="javascript: get_shapefile();" class="btn btn-default" type="button"><i class="fa fa-download"></i> Download Data</button>
    	</div>
    	</div><!-- ./q2 -->
    <div id="q3">
      <div id="detailsContainer">
		<div id="clickDetails" class="well">
		  <div id="details_loading" style="display: none;"><img src="/images/wait24trans.gif" /> Loading...</div>
		  <div id="details_details"></div>
		  <div id="details_hidden">Double click on a watershed to load detailed data</div>
		</div>
      </div><!-- ./detailsContainer -->
    </div><!-- ./q3 -->
    <div id="q4">

    <h4>Map Base Layers</h4>
        <ul id="ls-base-layers" class="list-unstyled"></ul>
    <h4>Map Overlay Layers</h4>
        <ul id="ls-overlay-layers" class="list-unstyled"></ul>

    </div><!-- ./q4 -->
</div><!-- ./sidebar-content -->

  </div><!--/.sidebar-->
 </div><!--/.row -->
</div><!--/.container-fluid -->

<div id="maptitlediv">
    <div class="row">
        <div class="col-xs-12"><span id="maptitle">DEP Map</span></div>
    </div>
</div>
<div id="fdetails">
    <div class="row">
      <div class="col-xs-12 col-md-4">
        <div class="row fshaded">
        	<div class="col-xs-12">HUC12: <span id="info-huc12"></span></div>
        	<div class="col-xs-6 col-md-12">Precipitation: <span class="visible-xs-inline"><br></span><span id="info-precip"></span></div>
        	<div class="col-xs-6 col-md-12">Water Runoff: <span class="visible-xs-inline"><br></span><span id="info-runoff"></span></div>
        	<div class="col-xs-6 col-md-12">Soil Detachment: <span class="visible-xs-inline"><br></span><span id="info-loss"></span></div>
        	<div class="col-xs-6 col-md-12">Hillslope Soil Loss: <span class="visible-xs-inline"><br></span><span id="info-delivery"></span></div>
        </div><!-- ./inner row container -->
       </div><!-- ./column container -->
    </div><!-- ./outer row container -->
</div>

    <!-- Placed at the end of the document so the pages load faster -->
    <!-- Careful of the order here as buttonset conflicts from jquery and bs -->
    <script src="/vendor/jquery/1.11.3/jquery-1.11.3.min.js"></script>
    <script src="/vendor/bootstrap/3.3.7/js/bootstrap.min.js"></script>
    <script src="/vendor/jquery-ui/1.11.4/jquery-ui.min.js"></script>
    <!-- IE10 viewport hack for Surface/desktop Windows 8 bug -->
    <script src="/vendor/bootstrap/3.3.7/js/ie10-viewport-bug-workaround.js"></script>
 	<script src='/vendor/openlayers/{$OL}/ol.js'></script>

        <script type="text/javascript">
var tilecache = "{$TMS_SERVER}";
var appstate = {
	lastdate: new Date("{$ddd}"),
	lat: {$lat},
	lon: {$lon},
	date: new Date("{$ddd}"),
	date2: null,
    metric: 0,
	ltype: 'qc_precip'
};
        </script>

    <script src="nextgen.js?v=2"></script>

</html>
EOM;
?>
