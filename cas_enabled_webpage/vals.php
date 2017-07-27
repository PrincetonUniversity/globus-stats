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
 
$data_location = "<DIRECTORY_WHERE_DATA_IS_LOCATED>";
//example: $data_location = "/data/";

$cas_users = file_get_contents($data_location . "auth_users.json");
$json_data = json_decode($cas_users,true);

$dtn_selections = file_get_contents($data_location . "dtn_selections.txt");
$dtn_name_uuid = json_encode(json_decode(file_get_contents($data_location . "dtn_name_uuid.json"),true));

$GLOBALS["authed"] = false;
$users_str = $json_data['auth_users'];
$users_list = explode(",",$users_str);
?>
