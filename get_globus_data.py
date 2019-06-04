################################################################################
# Python Script
#  - Description: Script for pulling Globus transfer data
#  - Author: Hyojoon Kim (joonk@princeton.edu)
################################################################################

################################################################################
# Copyright (C) 2017  Hyojoon Kim (Princeton University)
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
# 
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.
################################################################################



import argparse, pickle
import os,sys,copy,datetime, time,pytz, calendar
import json
import python_api
import csv_generation
import globus_sdk


def add_months(sourcedate,months):
    month = sourcedate.month - 1 + months
    year = int(sourcedate.year + month / 12 )
    month = month % 12 + 1
    day = min(sourcedate.day,calendar.monthrange(year,month)[1])

    return datetime.date(year,month,day)

def create_monthly_ts(first_date, last_date):
    created_timeseries_list = []

    now = first_date.date()
    while now < last_date.date():
        created_timeseries_list.append(time.mktime(now.timetuple()))
        now = add_months(now,1)

    return created_timeseries_list

def reformat_ts(first_date, last_date, sorted_datetime_per_endpoint):

    xfers_per_endpoint_map = {} # { Endpoint : list of transfers per day }
    total_per_day = 0

    # Create x-axis datetimes with timestamp (every day)
    now = time.mktime(first_date.timetuple())
    created_timeseries_list = []

    # Create a list of dates with an interval of 1 month between first and last date.
    created_timeseries_list = create_monthly_ts(first_date,last_date)

    # For each endpoint, go through the created timeseries and check/count if there was a transfer each day        
    for endpoint in sorted_datetime_per_endpoint.keys():
        xfers_per_endpoint_map[endpoint] = []

        # Go through created timeseries 
        for idx,timeval in enumerate(created_timeseries_list):
            count_instance_in_this_ts = 0
            created_ts = timeval

            # Check if there was a transfer this day by going through the list of transfers
            for ts in sorted_datetime_per_endpoint[endpoint]:
                tmp_ts = time.mktime(ts.timetuple())

                # When we started with a date with daylight saving and if daylight saving is not in effect now, substract 1 hour 
                # When we started with a date without daylight saving and if daylight saving is in effect now, add 1 hour 
                if ts.dst()==datetime.timedelta(hours=0) and first_date.dst()==datetime.timedelta(hours=1):
                    tmp_ts = tmp_ts - 3600
                elif ts.dst()==datetime.timedelta(hours=1) and first_date.dst()==datetime.timedelta(hours=0):
                    tmp_ts = tmp_ts + 3600

                created_date = datetime.datetime.fromtimestamp(created_ts)
                tmp_date = datetime.datetime.fromtimestamp(tmp_ts)

                # If this endpoint had a transfer task on this date, count up
                if created_date.year==tmp_date.year and created_date.month==tmp_date.month:
                    count_instance_in_this_ts = count_instance_in_this_ts + 1

            # Save information about how many transfers happened this day                    
            xfers_per_endpoint_map[endpoint].append(count_instance_in_this_ts)
    
    # Create for total
    endpoint_list = xfers_per_endpoint_map.keys()
    xfers_per_endpoint_map['total'] = []
    total_transfers = 0
    for i in range(len(created_timeseries_list)):
        total_per_day = 0
        for ep in endpoint_list :
            total_per_day += xfers_per_endpoint_map[ep][i]
        xfers_per_endpoint_map['total'].append(total_per_day)
        total_transfers += total_per_day

    print 'Number of total transfers so far:', total_transfers

    # Return
    return created_timeseries_list,xfers_per_endpoint_map


def create_list_of_dtns_for_select(admin_endpoint_map, output_dir):

    fd = open(output_dir + "./dtn_selections.txt", 'w+')
    fd.write("All")
    for ep in admin_endpoint_map:
        fd.write(","+str(admin_endpoint_map[ep]))
    fd.close()


def create_dtn_to_uuid_mapping(admin_endpoint_map, output_dir):
    admin_endpoint_str_to_uuid_map = {}

    for ep in admin_endpoint_map:
        admin_endpoint_str_to_uuid_map[str(admin_endpoint_map[ep])] = str(ep)

#    admin_endpoint_str_to_uuid_map['All'] = 'all'

    # save as json file
    fd = open(output_dir + "./dtn_name_uuid.json", 'w+')
    json.dump(admin_endpoint_str_to_uuid_map, fd)
    fd.close()


def get_dates_for_time_series(admin_endpoint_map, measurement_map_map, output_dir, gconfig):
    local_tz = pytz.timezone(gconfig['timezone'])
    first_date = (datetime.datetime.max - datetime.timedelta(days=1)).replace(tzinfo=pytz.utc).astimezone(local_tz)
    last_date = (datetime.datetime.min + datetime.timedelta(days=1)).replace(tzinfo=pytz.utc).astimezone(local_tz)
    y_map_of_lists = {}
    sorted_datetime_per_endpoint = {}

    # For each endpoint
    for endpoint in measurement_map_map:
        sorted_datetime_per_endpoint[endpoint] = []

        # Go through request datetimes and get date without hour, minute, second, and microsecond information.
        for dt in sorted(measurement_map_map[endpoint]["request_datetime"]):
            date = dt - datetime.timedelta(hours=dt.hour, minutes=dt.minute, seconds=dt.second, microseconds=dt.microsecond)
            sorted_datetime_per_endpoint[endpoint].append(date)

        # Get min and max ts
        if len(sorted_datetime_per_endpoint[endpoint])>0:
            if first_date > sorted_datetime_per_endpoint[endpoint][0]:
                first_date = sorted_datetime_per_endpoint[endpoint][0]
            if last_date < sorted_datetime_per_endpoint[endpoint][-1]:
                last_date = sorted_datetime_per_endpoint[endpoint][-1]

    return first_date, last_date, sorted_datetime_per_endpoint



def create_csv(admin_endpoint_map, measurement_map_map, endpoint_id_to_name_map, output_dir, gconfig):
 
    # Get times
    first_date, last_date, sorted_datetime_per_endpoint = get_dates_for_time_series(admin_endpoint_map, measurement_map_map, output_dir, gconfig)

    # Number of successful transfers on timeline. Reformat data for plotting along timeseries                
    created_timeseries_list, xfers_per_endpoint_map = reformat_ts(first_date, last_date, sorted_datetime_per_endpoint)

    # CSV file for # of tasks along time series
    csv_generation.create_csv_timeseries(xfers_per_endpoint_map, admin_endpoint_map, created_timeseries_list, output_dir, gconfig,last_days=365)

    for days in [0,30,60,90]:
        # CSV file for piechart on endpoint targets that are not administered by you
        csv_generation.create_csv_targets_by(xfers_per_endpoint_map, measurement_map_map, endpoint_id_to_name_map, \
                          'all', True, output_dir, gconfig, last_days=days)

        # CSV file for table of # transfer tasks, # files, dataset size. Each row will be a DTN
        csv_generation.create_csv_all_table(xfers_per_endpoint_map, admin_endpoint_map, measurement_map_map, \
                                            output_dir, gconfig, last_days=days)
    
        # CSV file for: Table-Endpoint pairs by activity level 
        csv_generation.create_csv_table_pair_activity(xfers_per_endpoint_map, admin_endpoint_map, measurement_map_map, \
                                                      endpoint_id_to_name_map, output_dir, gconfig, last_days=days)

        # CSV file for: Piechart-internal vs. external transfers
        csv_generation.create_csv_int_ext(xfers_per_endpoint_map, admin_endpoint_map, measurement_map_map, \
                                          endpoint_id_to_name_map, output_dir, gconfig,last_days=days)

        # CSV file for: Table-overall user stats
        csv_generation.create_csv_users_by(xfers_per_endpoint_map, measurement_map_map, endpoint_id_to_name_map, \
                              'all', output_dir,gconfig, last_days=days)

        # Create csv files for each endpoint 
        for ep in admin_endpoint_map:
            csv_generation.create_csv_targets_by(xfers_per_endpoint_map, measurement_map_map, endpoint_id_to_name_map, \
                                  admin_endpoint_map[ep], False, output_dir,gconfig, last_days=days)
    
            csv_generation.create_csv_users_by(xfers_per_endpoint_map, measurement_map_map, endpoint_id_to_name_map, \
                                  admin_endpoint_map[ep], output_dir,gconfig, last_days=days)


def get_globus_access_token(client_id):

    client = globus_sdk.NativeAppAuthClient(client_id)
    client.oauth2_start_flow()
#    client.oauth2_start_flow_native_app()

    authorize_url = client.oauth2_get_authorize_url()
    print('Please go to this URL and login: {0}'.format(authorize_url))
    
    # this is to work on Python2 and Python3 -- you can just use raw_input() or
    # # input() for your specific version
    get_input = getattr(__builtins__, 'raw_input', input)
    auth_code = get_input('Please enter the code you get after login here: ').strip()
    token_response = client.oauth2_exchange_code_for_tokens(auth_code)

    globus_auth_data = token_response.by_resource_server['auth.globus.org']
    globus_transfer_data = token_response.by_resource_server['transfer.api.globus.org']

    # most specifically, you want these tokens as strings
    auth_token = globus_auth_data['access_token']
    transfer_token = globus_transfer_data['access_token']

    return auth_token,transfer_token


def get_globus_access_token_client_credentials(gconfig):

    # Get secret
    if os.path.isfile(gconfig["client_secret"]):
        fd = open(gconfig["client_secret"], 'r')
        client_secret = fd.read()
        fd.close()
    else:
        print '"' + gconfig["client_secret"] + '"' + ' file does not exist. Exit.'
        sys.exit(1)

    client_secret = client_secret.rstrip('\n')

    # Get auth and transfer tokens    
    client = globus_sdk.ConfidentialAppAuthClient(gconfig["client_id"], client_secret)
    token_response = client.oauth2_client_credentials_tokens()
    globus_auth_data = token_response.by_resource_server['auth.globus.org']
    globus_transfer_data = token_response.by_resource_server['transfer.api.globus.org']

    auth_token = globus_auth_data['access_token']
    transfer_token = globus_transfer_data['access_token']

    return auth_token,transfer_token
    

def get_globus_data(auth_token,transfer_token, gconfig):

    admin_endpoint_map = {}
    endpoint_map_list_of_tasks = {}

    # GlobusAuthorizer 
    authorizer = globus_sdk.AccessTokenAuthorizer(transfer_token)
    tc = globus_sdk.TransferClient(authorizer=authorizer)

    # High level interface; provides iterators for list responses. 
    # Get endpoints administered by user with given tokens
    for ep in tc.endpoint_search(filter_scope="administered-by-me"):
        print("[{}] {}".format(ep["id"], ep["display_name"]))

        # Filter DTNs that are not in the list of interested DTNs
        if ep["id"] not in gconfig["interested_dtn_id_list"]:
            continue

        # Deal with when display name is none.
        admin_endpoint_map[ep["id"]] = ep["display_name"]
        if ep["display_name"] is None:
            if ep["canonical_name"] is not None:
                admin_endpoint_map[ep["id"]] = ep["canonical_name"]
            else: 
                admin_endpoint_map[ep["id"]] = str(ep["id"])

        task_list = []
        iter_paginated_res = (tc.endpoint_manager_task_list(num_results=None, filter_endpoint=ep["id"]))
        for p in iter_paginated_res:
            task_list.append(p.data)
        endpoint_map_list_of_tasks[ep["id"]] = task_list

        # Print total number of tasks per endpoint
        print "Number of tasks",len(task_list)

    return admin_endpoint_map, endpoint_map_list_of_tasks


def read_data_and_create_maps(endpoint_map_list_of_tasks, gconfig):

    endpoint_id_to_name_map = {}
    measurement_map_map = {}
    users_set = set()
    task_id_set = set()

    # Go over each endpoint and pick value for each field that we are interested.
    for endpoint in endpoint_map_list_of_tasks.keys():

        # Define dictionary and fields that we are interested in.
        measurement_map_map[endpoint] = {} 
        measurement_map_map[endpoint]["transfer_size"] = []
        measurement_map_map[endpoint]["transfer_duration"] = []
        measurement_map_map[endpoint]["effective_speed"] = []
        measurement_map_map[endpoint]["num_files"] = []
        measurement_map_map[endpoint]["owner_id"] = []
        measurement_map_map[endpoint]["owner_string"] = []
        measurement_map_map[endpoint]["request_datetime"] = []
        measurement_map_map[endpoint]["is_source"] = []
        measurement_map_map[endpoint]["target_dtn_id"] = []

        # Get tasks from this administered endpoint
        for task in endpoint_map_list_of_tasks[endpoint]:

#            # Remove duplicatesa ?
#            if task['task_id'] in task_id_set:
#                continue
#            task_id_set.add(task['task_id'])

            # Get only the "SUCCEEDED" ones for now.
            if task["status"] != "SUCCEEDED":
                continue

            # Exclude if this task was requested by users in the Exclude list (testers)
            if task["owner_id"] in gconfig["exclude_owner_id_list"]:
                continue

            # Exclude if this task's dataset size is 0
            if task["bytes_transferred"]==0:
                continue

            # Exclude dates (e.g., globus minicourse days)
            if task["request_time"][:10] in gconfig["exclude_date_list_startstring"]:
                continue

            # Exclude if effective speed is 0
            if task["effective_bytes_per_second"]==0:
                continue
            
            # Get source and dst DTN name
            source_dtn_name = task["source_endpoint_display_name"]
            dst_dtn_name = task["destination_endpoint_display_name"]

            # Skip ESnet test DTNs. They start with strings such as below.
            if source_dtn_name is not None and source_dtn_name.startswith('ESnet Read-Only Test DTN'):
                continue
            if dst_dtn_name is not None and dst_dtn_name.startswith('ESnet Read-Only Test DTN'):
                continue

            # Debug print message
            # print("Task({}): {} -> {} was submitted by {}".format(task["task_id"], task["source_endpoint"],task["destination_endpoint"], task["owner_string"]))
 
            # Get transfer size
            measurement_map_map[endpoint]["transfer_size"].append(task["bytes_transferred"])

            # Set local timezone as New York.
            local_tz = pytz.timezone(gconfig['timezone'])

            # Get times
            request_datetime = (datetime.datetime.strptime(task["request_time"], "%Y-%m-%dT%H:%M:%S+00:00")).replace(tzinfo=pytz.utc).astimezone(local_tz)
            completion_datetime = (datetime.datetime.strptime(task["completion_time"], "%Y-%m-%dT%H:%M:%S+00:00")).replace(tzinfo=pytz.utc).astimezone(local_tz)
            diff =  completion_datetime - request_datetime
            measurement_map_map[endpoint]["request_datetime"].append(request_datetime)
            measurement_map_map[endpoint]["transfer_duration"].append(diff.total_seconds())
    
            # Get transfer speed
            measurement_map_map[endpoint]["effective_speed"].append(task["effective_bytes_per_second"])

            # Get number of files
            measurement_map_map[endpoint]["num_files"].append(task["files_skipped"] + task["files_transferred"])

            # Get number of unique users     
            measurement_map_map[endpoint]["owner_id"].append(task["owner_id"])
            measurement_map_map[endpoint]["owner_string"].append(task["owner_string"])
            users_set.add(task["owner_id"])
            
            # To or from, and target DTN
            if task["source_endpoint_id"] == endpoint:
                measurement_map_map[endpoint]["is_source"].append(True)
                measurement_map_map[endpoint]["target_dtn_id"].append(task['destination_endpoint_id'])
            else:
                measurement_map_map[endpoint]["is_source"].append(False)
                measurement_map_map[endpoint]["target_dtn_id"].append(task['source_endpoint_id'])

            # Populate endpoint id to name mapping                
            endpoint_id_to_name_map[task['source_endpoint_id']] = task['source_endpoint_display_name']
            endpoint_id_to_name_map[task['destination_endpoint_id']] = task['destination_endpoint_display_name']

    return measurement_map_map, users_set, endpoint_id_to_name_map


def read_configuration_file(config_file):
    if config_file.endswith('globus_config_template.json'):
        print "Default configuration filename used (globus_config_template.json). \
               Please change filename. This is to prevent accidental upload to Github."
        sys.exit(-1)

    fd = open(config_file, 'r')
    tmp_list = fd.readlines()
    json_string = ""
    for l in tmp_list:
        if not l.startswith('#'):
            json_string += (l)
    json_string = json_string[:-1]
    gconfig = json.loads(json_string)
    fd.close()

    return gconfig


## Main function ##     
def main():

    parser = argparse.ArgumentParser(description='Script to pull Globus transfer data via REST calls')
    parser.add_argument('-c', dest='config_file', action='store', required=True,
                        help='Configuration file')
    parser.add_argument('-o', dest='output_dir', action='store', required=True,
                        help='Output directory')
    parser.add_argument('-n', action='store_true', 
                        help='Add this option if you want to fetch new data from Globus,\
                              not using the existing pickled data in the output directory')

    # Parse
    args = parser.parse_args()

    # Check number of arguments. 
    if len(sys.argv[1:])<4:
        print "\nERROR: Wrong number of parameters. -c and -o are required.\n"
        parser.print_help()
        sys.exit(0)

    # Reformat output directory, and check validity.        
    output_dir = python_api.check_directory_and_add_slash(args.output_dir)

    # Check validity of option values
    if os.path.isdir(output_dir) is False or os.path.isfile(args.config_file) is False:
        print "\nERROR: Specifid output directory or configuration file does not exist. Abort.\n" 
        parser.print_help()
        sys.exit(-1)

    # Read configuration
    gconfig = read_configuration_file(args.config_file)

    # Define data maps        
    admin_endpoint_map = {}          # { admin endpoint_UUID : endpoint_string_name }
    endpoint_id_to_name_map = {}     # { all endpoint_UUID : endpoint_string_name }
    endpoint_map_list_of_tasks = {}  # Raw data fetch from Globus. { admin endpoint_UUID : [ tasks ] }
    measurement_map_map = {}         # Processed data to produce stats. { admin endpoint_UUID : { field : [ values for each task ] } }
    users_set = set()                # Set of unique user IDs

    # Check if pulled data is present in output_dir. 
    # If they are all there, and option '-n' was not given, open and load them.
    dirs_list = os.listdir(output_dir)
    if args.n is False and 'endpoint_map_list_of_tasks.p' in dirs_list:
        print 'Using existing maps in directory: ' + str(output_dir)
        admin_endpoint_map = pickle.load(open(output_dir+'admin_endpoint_map.p', 'rb'))
        endpoint_map_list_of_tasks = pickle.load(open(output_dir+'endpoint_map_list_of_tasks.p', 'rb'))

    # Else, pull new data from Globus via REST call        
    else:
        print 'Pull new Globus data!'

        # Get data via REST call
        auth_token, transfer_token = get_globus_access_token_client_credentials(gconfig)
        admin_endpoint_map, endpoint_map_list_of_tasks = get_globus_data(auth_token, transfer_token, gconfig)

        # Save data in output directory.
        python_api.save_data_as_pickle(endpoint_map_list_of_tasks, 'endpoint_map_list_of_tasks', output_dir)
        python_api.save_data_as_pickle(admin_endpoint_map, 'admin_endpoint_map', output_dir)
       
    # Read raw data from Globus and create processed data dictionaries and sets.
    measurement_map_map, users_set, endpoint_id_to_name_map = read_data_and_create_maps(endpoint_map_list_of_tasks, gconfig)

    # Create CSV files (currently fit as input data for Google Chart)
    create_csv(admin_endpoint_map, measurement_map_map, endpoint_id_to_name_map, output_dir, gconfig)
 
    # Create files for html drawing
    create_list_of_dtns_for_select(admin_endpoint_map, output_dir)
    create_dtn_to_uuid_mapping(admin_endpoint_map, output_dir)

    # Print number of unique users    
    print 'Number of unique users:',len(users_set)


if __name__ == '__main__':
    main()


