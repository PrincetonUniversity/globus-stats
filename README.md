# Retrieving and plotting Globus usage logs

This Python script (1) pulls transfer logs from Globus.org, and (2) plots various graphs.

## Prerequisite
  - Environment to run Python code (tested with v2.7).
  - Python libraries: Pytz and Goblus-python-sdk. 
  - Web server with PHP (tested with EasyApache PHP 5.6 with cPanel, ea-php56).
  - Please read [Wiki](https://github.com/PrincetonUniversity/globus-stats/wiki) for more information on installation and setup.
  
## Demo website
  - See how it looks, live! (https://globusstat.cpaneldev.princeton.edu/demo/index.php)
  - Charts on user statistics are hidden for privacy, because they contain email addresses.

## Documentation (including generating and hosting charts on web server)
  - See the [Wiki](https://github.com/PrincetonUniversity/globus-stats/wiki) for more detailed documentation. 
  
## Basic usage of the script itself
  - `python get_globus_data.py -c <GLOBUS_CONFIG_FILE> -o <OUTPUT_DIRECTORY> [-n]`
  - Options inside `[]` are optional. Options inside `<>` are required.
  - Replace `<OUTPUT_FILE>` with a directory where you want to save the plot image files and pickled output data dictionary files.
  - Replace `<GLOBUS_CONFIG_FILE>` with your custom configuration file.
  - `-n` is for fetching new transfer task data from Globus instead of using the pickled data in the output directory. When used, `client.secret` file must be present in the location where the script is located. The correct password string for corresponding client should be written in this file (and only that). 
  - See the [Wiki](https://github.com/PrincetonUniversity/globus-stats/wiki) for more detailed documentation. 
  
## Important Notes
  - NEVER upload `client.secret` file (`client.secret` is in `.gitignore` for safety.). Never hardcode client secret passcode in any code that can get uploaded to Github. 
  - This work is licensed under the **GNU General Public License v3.0**. 
