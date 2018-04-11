################################################################################
# Python Script
#  - Description: Script for generating CSV files from globus 
#                 usage data.
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


import datetime,os,time,pytz
import stat


def create_csv_all_table(xfers_per_endpoint_map, admin_endpoint_map, measurement_map_map, output_dir, gconfig, last_days=0):

    # First line for CSV file
    csv_content = 'DTN,Number of Transfers (to/from),Number of Files (to/from),Dataset Size in GB (to/from)'

    # Totals
    total_files_to  = 0
    total_files_from = 0
    total_xfer_to  = 0
    total_xfer_from = 0
    total_size_GB_to  = 0
    total_size_GB_from = 0

    # For each endpoint,
    for ep in xfers_per_endpoint_map:
        if ep!='total':
            dtn_name = admin_endpoint_map[ep].encode('utf-8')
            files_to  = 0
            files_from = 0
            xfer_to  = 0
            xfer_from = 0
            size_GB_to  = 0
            size_GB_from = 0

            # Go through all tasks
            for idx in range(len(measurement_map_map[ep]['is_source'])):

                # time filter
                local_tz = pytz.timezone(gconfig['timezone'])

                if last_days!=0: 
                    nowdate = datetime.datetime.utcnow().replace(tzinfo=pytz.timezone(gconfig['timezone']))
                    end_datetime_tz = nowdate
                    start_datetime_tz = end_datetime_tz - datetime.timedelta(days=last_days)

                    if start_datetime_tz > measurement_map_map[ep]["request_datetime"][idx] or end_datetime_tz < measurement_map_map[ep]["request_datetime"][idx]:
                        continue

                if measurement_map_map[ep]['is_source'][idx] is True:
                    xfer_from += 1
                    files_from += (measurement_map_map[ep]['num_files'][idx])
                    size_GB_from += ((measurement_map_map[ep]['transfer_size'][idx])/1024.0/1024.0/1024.0)
                else:
                    xfer_to += 1 
                    files_to += (measurement_map_map[ep]['num_files'][idx])
                    size_GB_to += ((measurement_map_map[ep]['transfer_size'][idx])/1024.0/1024.0/1024.0)


            
            # Update total 
            total_files_to += files_to
            total_files_from += files_from
            total_xfer_to += xfer_to
            total_xfer_from += xfer_from
            total_size_GB_to += size_GB_to
            total_size_GB_from += size_GB_from

            # Create line for this endpoint
            csv_line = ",".join([dtn_name,str(xfer_to)+' / '+str(xfer_from),str(files_to)+' / '+str(files_from), "%.2f" % (size_GB_to)+' / '+ "%.2f" % (size_GB_from)])
            csv_content += ('\n' + csv_line)
    
    # Add Total. 
    csv_content += ('\n' + ','.join(['Total',str(total_xfer_to)+' / '+str(total_xfer_from),str(total_files_to)+' / '+str(total_files_from), "%.2f" % (total_size_GB_to)+' / '+ "%.2f" % (total_size_GB_from)]))

    # Save csv
    fobj = open(output_dir + 'table_all_' + str(last_days) + '.csv','w')
    fobj.write(csv_content)
    fobj.close()



def create_csv_users_by(xfers_per_endpoint_map, measurement_map_map, endpoint_id_to_name_map, \
                          dtn_name_str, output_dir, gconfig, last_days=0,\
                          start_datetime=datetime.datetime.min+datetime.timedelta(days=1), end_datetime=datetime.datetime.max-datetime.timedelta(days=1)):

    # local use
    list_of_dtns = []
    dtn_uuid = ''

    # Users map
    user_map_count = {}

    # Go through all administered DTNs or selected DTN
    if dtn_name_str=='all':
        list_of_dtns = xfers_per_endpoint_map.keys()
        dtn_uuid = 'All'
    else: 
        for uuid in endpoint_id_to_name_map:
            if endpoint_id_to_name_map[uuid] == dtn_name_str:
                list_of_dtns = [uuid]
                dtn_uuid = uuid
                break

    # If no dtn in list_of_dtns, there is no data for that dtn.
    if len(list_of_dtns) == 0:
        print 'Specified DTN (%s) does not have usage data'%(dtn_name_str)
        return

    # For each endpoint,
    for ep in list_of_dtns:
        if ep!='total':

            # Go through all tasks
            for idx in range(len(measurement_map_map[ep]['is_source'])):

                user_string = measurement_map_map[ep]['owner_string'][idx]

                # time filter
                local_tz = pytz.timezone(gconfig['timezone'])
                start_datetime_tz = start_datetime.replace(tzinfo=pytz.utc).astimezone(local_tz)
                end_datetime_tz = end_datetime.replace(tzinfo=pytz.utc).astimezone(local_tz)

                if last_days!=0: 
                    nowdate = datetime.datetime.utcnow().replace(tzinfo=pytz.timezone(gconfig['timezone']))
                    end_datetime_tz = nowdate
                    start_datetime_tz = end_datetime_tz - datetime.timedelta(days=last_days)

                if start_datetime_tz > measurement_map_map[ep]["request_datetime"][idx] or end_datetime_tz < measurement_map_map[ep]["request_datetime"][idx]:
                    continue

                # Get numbers
                xfers = 1
                nfiles = (measurement_map_map[ep]['num_files'][idx])
                size_GB = ((measurement_map_map[ep]['transfer_size'][idx])/1024.0/1024.0/1024.0)

                # Update
                if user_map_count.has_key(user_string):
                    user_map_count[user_string]['num_xfers'] += 1
                    user_map_count[user_string]['num_files'] += nfiles
                    user_map_count[user_string]['transfer_size'] += size_GB
                else:
                    user_map_count[user_string] = {}
                    user_map_count[user_string]['num_xfers'] = 1
                    user_map_count[user_string]['num_files'] = nfiles
                    user_map_count[user_string]['transfer_size'] = size_GB


    # First line for CSV file
    csv_content_xfers = 'User,Total # of Transfers (to+from)'
    csv_content_files = 'User,Total # of files'
    csv_content_sizes = 'User,Total size(GB)'
    csv_content_all = 'User,Total # of Transfers (to+from),Total # of files,Total size(GB)'

    # Add line for each user.
    for user in user_map_count:
        csv_content_xfers += ('\n' + user + ',' + str(user_map_count[user]['num_xfers']))
        csv_content_files += ('\n' + user + ',' + str(user_map_count[user]['num_files']))
        csv_content_sizes += ('\n' + user + ',' + '{0:.2f}'.format(user_map_count[user]['transfer_size']))
        csv_content_all += ('\n' + user + ',' + str(user_map_count[user]['num_xfers'])+ ',' + str(user_map_count[user]['num_files'])+ ',' + '{0:.2f}'.format(user_map_count[user]['transfer_size']))

    csv_content_str_map = {}
    csv_content_str_map['num_xfers'] = csv_content_xfers
    csv_content_str_map['num_files'] = csv_content_files
    csv_content_str_map['transfer_size'] = csv_content_sizes
    csv_content_str_map['all'] = csv_content_all

    for c in csv_content_str_map:
        # Save csv
        fobj = open(output_dir + 'users_' + dtn_uuid + '_' + str(last_days) + "_" + c + '.csv', 'w')
        fobj.write(csv_content_str_map[c])
        fobj.close()


def create_csv_targets_by(xfers_per_endpoint_map, measurement_map_map, endpoint_id_to_name_map, \
                          dtn_name_str, exclude_admin_dtns, output_dir, gconfig, last_days=0,\
                          start_datetime=datetime.datetime.min+datetime.timedelta(days=1), end_datetime=datetime.datetime.max-datetime.timedelta(days=1)):

    # local use
    list_of_dtns = []
    dtn_uuid = ''

    # Target DTN : number_of_xfers
    target_map_count = {}

    # Go through all administered DTNs or selected DTN
    if dtn_name_str=='all':
        list_of_dtns = xfers_per_endpoint_map.keys()
        dtn_uuid = 'All'
    else: 
        for uuid in endpoint_id_to_name_map:
            if endpoint_id_to_name_map[uuid] == dtn_name_str:
                list_of_dtns = [uuid]
                dtn_uuid = uuid
                break

    # If no dtn in list_of_dtns, there is no data for that dtn.
    if len(list_of_dtns) == 0:
        print 'Specified DTN (%s) does not has usage data'%(dtn_name_str)
        return

    # For each endpoint,
    for ep in list_of_dtns:
        if ep!='total':

            # Go through all tasks
            for idx in range(len(measurement_map_map[ep]['is_source'])):

                target_dtn_id = measurement_map_map[ep]['target_dtn_id'][idx]
                if exclude_admin_dtns is True: 
                    if target_dtn_id in gconfig["interested_dtn_id_list"]:
                        continue

                # time filter
                local_tz = pytz.timezone(gconfig['timezone'])
                start_datetime_tz = start_datetime.replace(tzinfo=pytz.utc).astimezone(local_tz)
                end_datetime_tz = end_datetime.replace(tzinfo=pytz.utc).astimezone(local_tz)

                if last_days!=0: 
                    nowdate = datetime.datetime.utcnow().replace(tzinfo=pytz.timezone(gconfig['timezone']))
#                    nowdate = nowdate + datetime.timedelta(days=1) - datetime.timedelta(hours=nowdate.hour, minutes=nowdate.minute, seconds=nowdate.second, microseconds=nowdate.microsecond)
                    end_datetime_tz = nowdate
                    start_datetime_tz = end_datetime_tz - datetime.timedelta(days=last_days)

                if start_datetime_tz > measurement_map_map[ep]["request_datetime"][idx] or end_datetime_tz < measurement_map_map[ep]["request_datetime"][idx]:
                    continue

                # Get numbers
                xfers = 1
                nfiles = (measurement_map_map[ep]['num_files'][idx])
                size_GB = ((measurement_map_map[ep]['transfer_size'][idx])/1024.0/1024.0/1024.0)

                # Update
                if target_map_count.has_key(endpoint_id_to_name_map[target_dtn_id]):
                    target_map_count[endpoint_id_to_name_map[target_dtn_id]]['num_xfers'] += 1
                    target_map_count[endpoint_id_to_name_map[target_dtn_id]]['num_files'] += nfiles
                    target_map_count[endpoint_id_to_name_map[target_dtn_id]]['transfer_size'] += size_GB
                else:
                    target_map_count[endpoint_id_to_name_map[target_dtn_id]] = {}
                    target_map_count[endpoint_id_to_name_map[target_dtn_id]]['num_xfers'] = 1
                    target_map_count[endpoint_id_to_name_map[target_dtn_id]]['num_files'] = nfiles
                    target_map_count[endpoint_id_to_name_map[target_dtn_id]]['transfer_size'] = size_GB


    # First line for CSV file
    csv_content_xfers = 'DTN,Total # of Transfers (to+from)'
    csv_content_files = 'DTN,Total # of files'
    csv_content_sizes = 'DTN,Total size(GB)'
    csv_content_all = 'DTN,Total # of Transfers (to+from),Total # of files,Total size(GB)'
    
    # Add line for each target endpoint. 
    for ep in target_map_count:
        dtn = ep
        if ep==None:
            dtn = 'Private endpoint'

        csv_content_xfers += ('\n' + dtn + ',' + str(target_map_count[ep]['num_xfers']))
        csv_content_files += ('\n' + dtn + ',' + str(target_map_count[ep]['num_files']))
        csv_content_sizes += ('\n' + dtn + ',' + '{0:.2f}'.format(target_map_count[ep]['transfer_size']))
        csv_content_all += ('\n' + dtn + ',' + str(target_map_count[ep]['num_xfers'])+ ',' + str(target_map_count[ep]['num_files'])+ ',' + '{0:.2f}'.format(target_map_count[ep]['transfer_size']))

    csv_content_str_map = {}
    csv_content_str_map['num_xfers'] = csv_content_xfers
    csv_content_str_map['num_files'] = csv_content_files
    csv_content_str_map['transfer_size'] = csv_content_sizes
    csv_content_str_map['all'] = csv_content_all

    for c in csv_content_str_map:
        # Save csv
        fobj = open(output_dir + 'targets_' + dtn_uuid + '_' + str(last_days) + '_' + c + '.csv', 'w')
        fobj.write(csv_content_str_map[c])
        fobj.close()


def create_csv_timeseries(xfers_per_endpoint_map, admin_endpoint_map, created_timeseries_list, output_dir, gconfig, last_days):

    # Get endpoints
    endpoint_list = []
    for ep in xfers_per_endpoint_map:
        if ep!='total':
            endpoint_list.append(admin_endpoint_map[ep].encode('utf-8'))

    # First line for CSV file
    csv_content = "Date," + (",".join(endpoint_list)) + ",Total"

    # for 
    for idx,timeval in enumerate(created_timeseries_list):
        value_list = []

        if last_days!=0: 
            nowdate = datetime.datetime.utcnow().replace(tzinfo=pytz.timezone(gconfig['timezone']))
            end_datetime_tz = nowdate
            start_datetime_tz = end_datetime_tz - datetime.timedelta(days=last_days)
            this_timeval = datetime.datetime.fromtimestamp(timeval)

            # Creat datetime with day set to 1 (so that when we compare dates, only year and month values are relevant)
            start_yearmonth = datetime.datetime(year=start_datetime_tz.year, month=start_datetime_tz.month, day=1)
            this_yearmonth = datetime.datetime(year=this_timeval.year, month=this_timeval.month, day=1)

            # Filter out dates that are older than start_yearmonth
            if start_yearmonth > this_yearmonth:
                continue

        # Convert timestamp to date string
        date_str = datetime.datetime.fromtimestamp(timeval).strftime('%m/%Y')
        value_list.append(date_str)
    
        # Value per endpoint for this date
        for endpoint in xfers_per_endpoint_map:
            if endpoint!='total':
                num_tasks = xfers_per_endpoint_map[endpoint][idx]
                value_list.append(str(num_tasks))

        # Add Total as last entry
        value_list.append(str(xfers_per_endpoint_map['total'][idx]))

        # Create csv line.            
        csv_line = ','.join(value_list)

        # Add csv_line
        csv_content += ('\n' + csv_line)

#    print csv_content
    
    # Save csv
    fobj = open(output_dir + 'timeseries.csv','w')
    fobj.write(csv_content)
    fobj.close()


def create_csv_table_pair_activity(xfers_per_endpoint_map, admin_endpoint_map, measurement_map_map, endpoint_id_to_name_map, output_dir, gconfig, last_days=0):
    csv_content = ""

    # dtn-pair (set) : pair_data_map
    pair_to_stat_map = {}

    # First line for CSV file
    csv_content = 'DTN Pair,Total # of Transfers (to+from),Total # of files,Total size(GB)'

    # For each endpoint,
    for ep in xfers_per_endpoint_map:
        if ep!='total':

            # Go through all tasks
            for idx in range(len(measurement_map_map[ep]['is_source'])):

                # Get target endpooint and create pair
                target_id = measurement_map_map[ep]['target_dtn_id'][idx]
                if target_id == None:
                    target_id = 'Private'
                dtn_pair = tuple(sorted([ep,target_id]))

                # time filter
                local_tz = pytz.timezone(gconfig['timezone'])

                if last_days!=0: 
                    nowdate = datetime.datetime.utcnow().replace(tzinfo=pytz.timezone(gconfig['timezone']))
                    end_datetime_tz = nowdate
                    start_datetime_tz = end_datetime_tz - datetime.timedelta(days=last_days)

                    if start_datetime_tz > measurement_map_map[ep]["request_datetime"][idx] or end_datetime_tz < measurement_map_map[ep]["request_datetime"][idx]:
                        continue

                # Get numbers
                xfers = 1
                nfiles = (measurement_map_map[ep]['num_files'][idx])
                size_GB = ((measurement_map_map[ep]['transfer_size'][idx])/1024.0/1024.0/1024.0)

                # If not already there, create and initialize
                if not pair_to_stat_map.has_key(dtn_pair):
                    pair_to_stat_map[dtn_pair] = {}
                    pair_to_stat_map[dtn_pair]['total_transfers'] = 0
                    pair_to_stat_map[dtn_pair]['total_files'] = 0
                    pair_to_stat_map[dtn_pair]['total_size_GB'] = 0

                # Update pair's data
                pair_to_stat_map[dtn_pair]['total_transfers'] += xfers
                pair_to_stat_map[dtn_pair]['total_files'] += nfiles
                pair_to_stat_map[dtn_pair]['total_size_GB'] += size_GB
            
    # Now go through and create lines
    for pair in pair_to_stat_map:
        if pair[0] == 'Private':
            dtn1_name = 'Private endpoint'
        else: 
            dtn1_name = endpoint_id_to_name_map[pair[0]].encode('utf-8')
        if pair[1] == 'Private':
            dtn2_name = 'Private endpoint'
        else: 
            dtn2_name = endpoint_id_to_name_map[pair[1]].encode('utf-8')

        csv_line = ",".join([dtn1_name+' -- '+dtn2_name, str(pair_to_stat_map[pair]['total_transfers']), str(pair_to_stat_map[pair]['total_files']), '%.2f' % (pair_to_stat_map[pair]['total_size_GB'])])

        csv_content += ('\n' + csv_line)

    # Save csv
    fobj = open(output_dir + 'table_pair_activity_' + str(last_days) + '.csv','w')
    fobj.write(csv_content)
    fobj.close()



def create_csv_int_ext(xfers_per_endpoint_map, admin_endpoint_map, measurement_map_map, endpoint_id_to_name_map, output_dir, gconfig, last_days=0):

    csv_content = ""

    # dtn-pair (set) : pair_data_map
    int_ext_count_map = {}
    int_ext_count_map["Unknown (Private endpoint)"] = 0
    int_ext_count_map["Within Campus"] = 0
    int_ext_count_map["Campus -- Outside"] = 0

    # First line for CSV file
    csv_content = 'Within or inter,Total Size (GB)'

    # For each endpoint,
    for ep in xfers_per_endpoint_map:
        if ep!='total':

            # Go through all tasks
            for idx in range(len(measurement_map_map[ep]['is_source'])):

                # time filter
                local_tz = pytz.timezone(gconfig['timezone'])

                if last_days!=0: 
                    nowdate = datetime.datetime.utcnow().replace(tzinfo=pytz.timezone(gconfig['timezone']))
                    end_datetime_tz = nowdate
                    start_datetime_tz = end_datetime_tz - datetime.timedelta(days=last_days)

                    if start_datetime_tz > measurement_map_map[ep]["request_datetime"][idx] or end_datetime_tz < measurement_map_map[ep]["request_datetime"][idx]:
                        continue

                # Get numbers
                xfers = 1
                nfiles = (measurement_map_map[ep]['num_files'][idx])
                size_GB = ((measurement_map_map[ep]['transfer_size'][idx])/1024.0/1024.0/1024.0)

                # Get target endpooint and create pair
                target_id = measurement_map_map[ep]['target_dtn_id'][idx]
                if target_id == None:
                    target_id = 'Private'
                    int_ext_count_map["Unknown (Private endpoint)"] += size_GB
                elif target_id in gconfig["interested_dtn_id_list"]:
                    int_ext_count_map["Within Campus"] += size_GB
                else: 
                    int_ext_count_map["Campus -- Outside"] += size_GB

    # Now go through and create lines
    for type_xfer in int_ext_count_map:
        csv_line = ",".join([type_xfer, '%.2f' % (int_ext_count_map[type_xfer])])

        csv_content += ('\n' + csv_line)

    # Save csv
    fobj = open(output_dir + 'overall_int_ext_' + str(last_days) + '.csv','w')
    fobj.write(csv_content)
    fobj.close()



def create_csv_overall_user(xfers_per_endpoint_map, admin_endpoint_map, measurement_map_map, endpoint_id_to_name_map, output_dir, gconfig):
    csv_content = ""

    # owner : stats
    owner_to_stat_map = {}

    # First line for CSV file
    csv_content = 'User,Total # of Transfers (to+from),Total # of files,Total size(GB)'

    # For each endpoint,
    for ep in xfers_per_endpoint_map:
        if ep!='total':

            # Go through all tasks
            for idx in range(len(measurement_map_map[ep]['is_source'])):

                # Get owner
                owner_string = measurement_map_map[ep]['owner_string'][idx]

                # Get numbers
                xfers = 1
                nfiles = (measurement_map_map[ep]['num_files'][idx])
                size_GB = ((measurement_map_map[ep]['transfer_size'][idx])/1024.0/1024.0/1024.0)

                # If not already there, create and initialize
                if not owner_to_stat_map.has_key(owner_string):
                    owner_to_stat_map[owner_string] = {}
                    owner_to_stat_map[owner_string]['total_transfers'] = 0
                    owner_to_stat_map[owner_string]['total_files'] = 0
                    owner_to_stat_map[owner_string]['total_size_GB'] = 0

                # Update pair's data
                owner_to_stat_map[owner_string]['total_transfers'] += xfers
                owner_to_stat_map[owner_string]['total_files'] += nfiles
                owner_to_stat_map[owner_string]['total_size_GB'] += size_GB
            
    # Now go through and create lines
    for owner in owner_to_stat_map:
        csv_line = ",".join([owner, str(owner_to_stat_map[owner]['total_transfers']), str(owner_to_stat_map[owner]['total_files']), '%.2f' % (owner_to_stat_map[owner]['total_size_GB'])])

        csv_content += ('\n' + csv_line)

    # Save csv
    fobj = open(output_dir + 'overall_user.csv','w')
    fobj.write(csv_content)
    fobj.close()

