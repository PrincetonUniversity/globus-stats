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
include_once('CAS.php');
include("vals.php");
 
//phpCAS::setDebug();
 
// initialize phpCAS
phpCAS::client(CAS_VERSION_2_0,$json_data['cas_url'],443,'cas');
 
// no SSL validation for the CAS server
phpCAS::setNoCasServerValidation();
 
// force CAS authentication
phpCAS::forceAuthentication();
 
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

$param1 = json_decode($_GET['param1']);
$phpArray = array();
$var_str="x";
foreach ($param1 as $value) {
    $var_str = file_get_contents($data_location . "$value.csv");
    array_push($GLOBALS['phpArray'],$var_str);
}

$json_str = json_encode($phpArray);
echo $json_str;

?>
