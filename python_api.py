#################################################
# (c)  Copyright 2014 Hyojoon Kim
# All Rights Reserved 
# 
# email: deepwater82@gmail.com
#################################################

################################################################################
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


import sys
import os
import pickle
import re
import operator

def check_directory_and_add_slash(path):
  return_path = path

  # No path given  
  if return_path == None:
    print "None is given as path. Check given parameter."
    return ''
    
  # Path is not a directory, or does not exist.  
  if os.path.isdir(return_path) is False:
    print "Path is not a directory, or does not exist.: '%s'. Abort" % (return_path)
    return ''

  # Add slash if not there.  
  if return_path[-1] != '/':
    return_path = return_path + '/'

  # Return
  return return_path

def save_data_as_pickle(data, filename, output_dir):
  print '\nSaving Result: %s\n' %(str(filename) + '.p')
  pickle_fd = open(str(output_dir) + str(filename) + '.p','wb')
  pickle.dump(data,pickle_fd)
  pickle_fd.close()

  return


def sort_map_by_value(the_map):

  # list of tuples (key, value)
  sorted_tup = sorted(the_map.iteritems(), key=operator.itemgetter(1), reverse=True)

  # Returns a list of tuples [(key, value),]
  return sorted_tup
