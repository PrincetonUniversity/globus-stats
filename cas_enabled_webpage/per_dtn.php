<?php
//################################################################################
//# Copyright (C) 2017  Hyojoon Kim (Princeton University)
//#
//# This program is free software: you can redistribute it and/or modify it under
//# the terms of the GNU General Public License as published by the Free Software
//# Foundation, either version 3 of the License, or (at your option) any later
//# version.
//# 
//# This program is distributed in the hope that it will be useful, but WITHOUT
//# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
//# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
//# 
//# You should have received a copy of the GNU General Public License along
//# with this program.  If not, see <http://www.gnu.org/licenses/>.
//################################################################################

//
// phpCAS simple client
//
// import phpCAS lib
include_once('/usr/CAS/callCAS.php'); # Princeton OIT-specific CAS PHP
include("vals.php");
 
//phpCAS::setDebug();
 
// Below phpCAS calls are not required 
//  since OIT's callCAS.php (above) call them already

// initialize phpCAS
//phpCAS::client(CAS_VERSION_2_0,$json_data['cas_url'],443,'cas');
 
// no SSL validation for the CAS server
//phpCAS::setNoCasServerValidation();
 
// force CAS authentication
//phpCAS::forceAuthentication();
 
// at this step, the user has been authenticated by the CAS server
// and the user's login name can be read with phpCAS::getUser().
$GLOBALS["authed"] = false;
foreach ($users_list as $user) {
    if (phpCAS::getUser()==$user) {
        $GLOBALS["authed"] = true;
        break;
    }
}
if ($GLOBALS["authed"] == false) {
    header("Location: ./nopermission.php"); /* Redirect browser */
    exit();
}

// logout if desired
if (isset($_REQUEST['logout'])) {
 phpCAS::logout();
}
?>



<html>
  <head>
   <title>Globus Usage Statistics</title>
    <!--Load the AJAX API-->
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/2.1.4/jquery.min.js"></script>
    <script src="jquery.csv.min.js"></script>
    <script type="text/javascript" src="https://www.google.com/jsapi"></script>

    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.5/css/bootstrap.min.css">
    <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.5/js/bootstrap.min.js"></script>

    <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
    <script type="text/javascript">

      // Get parameter
      var param_str = window.location.search.substr(1);
      var param_str_list = param_str.split("&");
      var dtn_name = param_str_list[0].split("=")[1];

      // Load the Visualization API and the corechart package.
      google.charts.load('current', {'packages':['corechart', 'table']});

      if (dtn_name!="") {
        // Set a callback to run when the Google Visualization API is loaded.
        google.charts.setOnLoadCallback(function(){ drawChart(dtn_name); });
      }

      // Draw newly dtn is specified.
      function onSelectDTN(value)
      {
        if (value == "All") { 
          window.location.href = "./index.php";
        }
        else {
          var daterangeList =  document.getElementById("daterange");
          var daterange_str = daterangeList.options[daterangeList.selectedIndex].value;

          if (daterange_str=='All') {
            drawChart(value, '30');
          }
          else {
            drawChart(value, daterange_str);
          }
        }
      }

      // Draw newly dtn is specified.
      function onSelectDateRange(value)
      {
        var selDTNList =  document.getElementById("dtn_selections");
        var dtn_name_str = selDTNList.options[selDTNList.selectedIndex].value;

        if (value=='All') {
          drawChart(dtn_name_str, 30);
        }
        else {
          drawChart(dtn_name_str, value);
        }
      }


      // Draw chart by dtn selection
      function drawChart(dtn_name,last_days=30) {

        var selectList =  document.getElementById("dtn_selections");
        if (selectList!=null & selectList.length==1) {
          //Create array of options to be added
          var array = "<?php echo $dtn_selections; ?>".split(",")
          
          //Create and append the options
          for (var i = 0; i < array.length; i++) {
            var option = document.createElement("option");
            option.setAttribute("value", array[i]);
            option.text = array[i];
            selectList.appendChild(option);
            if (encodeURIComponent(array[i])==dtn_name) {
              var index = i;
            }
          }

          selectList.remove("Please choose from above");
          selectList.selectedIndex = index;
        }

        // Get DTN's UUID
        var dtn = JSON.parse('<?php echo $dtn_name_uuid; ?>');
        if (dtn_name != "All") {
          var dtn_uuid = dtn[decodeURI(dtn_name)];
        }
//          console.log(dtn_uuid);

        // Create array
        var request_array = JSON.stringify(["timeseries",
                                            "targets_" + dtn_uuid + "_" + last_days + "_num_xfers",
                                            "targets_" + dtn_uuid + "_" + last_days + "_num_files",
                                            "targets_" + dtn_uuid + "_" + last_days + "_transfer_size",
                                            "targets_" + dtn_uuid + "_" + last_days + "_all",
                                            "users_" + dtn_uuid + "_" + last_days + "_num_xfers",
                                            "users_" + dtn_uuid + "_" + last_days + "_num_files",
                                            "users_" + dtn_uuid + "_" + last_days + "_transfer_size",
                                            "users_" + dtn_uuid + "_" + last_days + "_all"]);

        var result = $.ajax({url: "getdata.php", 
                           data: { param1: request_array}, 
      		           type: "GET", async: false}).responseText;

        var response_array = JSON.parse(result);

	// * Number of transfers per month
        // transform the CSV string into a 2-dimensional array
        var arrayData = $.csv.toArrays(response_array[0], {onParseValue: $.csv.hooks.castToScalar});
        // this new DataTable object holds all the data
        var data = new google.visualization.arrayToDataTable(arrayData);
        var chart = new google.visualization.LineChart(document.getElementById('chart_div1'));
        var ts_options = {'title':'Number of tranfers per month','titleTextStyle': {fontSize:16}};
        chart.draw(data, ts_options);

	// * Activity stats Target 1
        // transform the CSV string into a 2-dimensional array
        var arrayData = $.csv.toArrays(response_array[1], {onParseValue: $.csv.hooks.castToScalar});
        // this new DataTable object holds all the data
        var data = new google.visualization.arrayToDataTable(arrayData);
        var chart = new google.visualization.PieChart(document.getElementById('chart_div2'));

        // Set chart options
        var pie1_options = {'title':'Target by number of transfers',
                       'width':600,'titleTextStyle': {fontSize:16},
                       'height':600};
        chart.draw(data, pie1_options);

	// * Activity stats Target 2
        // transform the CSV string into a 2-dimensional array
        var arrayData = $.csv.toArrays(response_array[2], {onParseValue: $.csv.hooks.castToScalar});
        // this new DataTable object holds all the data
        var data = new google.visualization.arrayToDataTable(arrayData);
        var chart = new google.visualization.PieChart(document.getElementById('chart_div3'));

        // Set chart options
        var pie1_options = {'title':'Target by transferred number of files',
                       'width':600, 'titleTextStyle': {fontSize:16},
                       'height':600};
        chart.draw(data, pie1_options);

	// * Activity stats Target 3
        // transform the CSV string into a 2-dimensional array
        var arrayData = $.csv.toArrays(response_array[3], {onParseValue: $.csv.hooks.castToScalar});
        // this new DataTable object holds all the data
        var data = new google.visualization.arrayToDataTable(arrayData);
        var chart = new google.visualization.PieChart(document.getElementById('chart_div4'));

        // Set chart options
        var pie1_options = {'title':'Target by transferred dataset size (GB)',
                       'width':600, 'titleTextStyle': {fontSize:16},
                       'height':600};
        chart.draw(data, pie1_options);

        // * Activity stats per target DTN
        // transform the CSV string into a 2-dimensional array
        var arrayData = $.csv.toArrays(response_array[4], {onParseValue: $.csv.hooks.castToScalar});
        // this new DataTable object holds all the data
        var data = new google.visualization.arrayToDataTable(arrayData);
        var chart = new google.visualization.Table(document.getElementById('chart_div5'));

        // Set chart options
        var table1_options = {'title':'Targets'};
        chart.draw(data, table1_options);

        // * Activity stats User 1
        // transform the CSV string into a 2-dimensional array
        var arrayData = $.csv.toArrays(response_array[5], {onParseValue: $.csv.hooks.castToScalar});
        // this new DataTable object holds all the data
        var data = new google.visualization.arrayToDataTable(arrayData);
        var chart = new google.visualization.PieChart(document.getElementById('chart_div6'));

        // Set chart options
        var pie1_options = {'title':'Users by number of transfers',
                       'width':600, 'titleTextStyle': {fontSize:16},
                       'height':600};
        chart.draw(data, pie1_options);

        // * Activity stats User 2
        // transform the CSV string into a 2-dimensional array
        var arrayData = $.csv.toArrays(response_array[6], {onParseValue: $.csv.hooks.castToScalar});
        // this new DataTable object holds all the data
        var data = new google.visualization.arrayToDataTable(arrayData);
        var chart = new google.visualization.PieChart(document.getElementById('chart_div7'));

        // Set chart options
        var pie1_options = {'title':'Users by transferred number of files',
                       'width':600, 'titleTextStyle': {fontSize:16},
                       'height':600};
        chart.draw(data, pie1_options);

        // * Activity stats User 3
        // transform the CSV string into a 2-dimensional array
        var arrayData = $.csv.toArrays(response_array[7], {onParseValue: $.csv.hooks.castToScalar});
        // this new DataTable object holds all the data
        var data = new google.visualization.arrayToDataTable(arrayData);
        var chart = new google.visualization.PieChart(document.getElementById('chart_div8'));

        // Set chart options
        var pie1_options = {'title':'Users by transferred dataset size (GB)',
                       'width':600, 'titleTextStyle': {fontSize:16},
                       'height':600};
        chart.draw(data, pie1_options);

        // * Activity stats per user table
        // transform the CSV string into a 2-dimensional array
        var arrayData = $.csv.toArrays(response_array[8], {onParseValue: $.csv.hooks.castToScalar});
        // this new DataTable object holds all the data
        var data = new google.visualization.arrayToDataTable(arrayData);
        var chart = new google.visualization.Table(document.getElementById('chart_div9'));

        // Set chart options
        var table1_options = {'title':'Users'};
	chart.draw(data, table1_options);
      }

    </script>
  </head>

  <body style="margin:10;padding:10">
    <!--Div that will hold the pie chart-->
    <div id="chart_div1"></div>

    <h3> Select DTN:
    <select id="dtn_selections" onchange="onSelectDTN(this.value)">
      <option>Please choose from above</option>
    </select>
    </h3>

    <h3> Select date range:
    <select id="daterange" onchange="onSelectDateRange(this.value)">
 <!--     <option value="All">All</option> --!>
      <option value="30">Last 30 days</option>
      <option value="60">Last 60 days</option>
      <option value="90">Last 90 days</option>
    </select>
    </h3>

    <br>
    <br>
    <h3> <b>Activity stats: Target</b> </h3>
    <div style="width: 100%; overflow: hidden;">
        <div id="chart_div2" style="width: 33%; float: left;"> Left </div>
        <div id="chart_div3" style=" display: inline-block; width:33%;"> middle </div>
        <div id="chart_div4" style="width: 33%; float: right;"> right </div>
    </div>

    <h3> <b>Activity stats per target DTN</b> </h3>
    <div id="chart_div5"></div>

    <br>
    <br>
    <h3> <b>Activity stats: User</b> </h3>
    <div style="width: 100%; overflow: hidden;">
        <div id="chart_div6" style="width: 33%; float: left;"> Left </div>
        <div id="chart_div7" style=" display: inline-block; width:33%;"> middle </div>
        <div id="chart_div8" style="width: 33%; float: right;"> right </div>
    </div>

    <h3> <b>Activity stats per user</b> </h3>
    <div id="chart_div9"></div>

  </body>
</html>
