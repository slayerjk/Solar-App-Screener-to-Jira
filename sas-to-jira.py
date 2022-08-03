#!/usr/bin/env python3

'''
This script is automatization of creating Jira tickets,
based on Solar AppScreener scan results.
'''

import logging
from datetime import datetime, date
import shutil
from time import sleep
from os import mkdir, path, remove
from sys import exit
from pathlib import Path
import requests
from json import loads, dumps
from zipfile import ZipFile
try:
    from pandas import read_csv, DataFrame
except Exception as error:
    logging.exception('FAILED: MODULE pandas MUST BE INSTALLED(pip3 install pandas)')

### DEFINING WORK DIR(SCRIPT'S LOCATION) ###
work_dir = '<your-path>'

###########################
##### LOGGING SECTION #####
today = datetime.now()
jira_date_format = date.today()

logs_dir = work_dir+'/logs'

if not path.isdir(logs_dir):
    mkdir(logs_dir)

app_log_name = logs_dir+'/sas-to-jira_log_' + \
    str(today.strftime('%d-%m-%Y'))+'.log'
logging.basicConfig(filename=app_log_name, filemode='w', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%b-%Y %H:%M:%S')
logging.info('SCRIPT WORK STARTED: SAS REPORT TO JIRA TICKET')
logging.info('Script Starting Date&Time is: ' +
             str(today.strftime('%d/%m/%Y %H:%M:%S')) + '\n')

######################################################################
##### DEFINING ALL NECESSARRY FOLDERS/FILES & API URLS VARIABLES #####

### DEFINING SOLARAPPSCREENER(SAS) FOLDERS ###
sas_files_dir = work_dir+'/sas_files'
temp_files_dir = work_dir+'/temp_files'
sas_reports = sas_files_dir+'/reports'
sas_json_templates = sas_files_dir+'/json-templates'

### LIST OF FOLDERS TO CREATE(CHECK FOLDER ABOVE) ###
list_of_folders = [sas_files_dir, sas_reports, sas_json_templates, temp_files_dir]

### DEFINING FILES VARIABLES ###
sas_api_token_file = sas_files_dir+'/sas-api-token.txt'
sas_download_csv_report_json_template = sas_json_templates+'/sas_download-csv-report_template.txt'
sas_report_zip = sas_reports+'/report'+'_'+str(jira_date_format)+'.zip'
jira_task_template = sas_json_templates+'/jira-task-template.json'

### TEMPORARY FILES(WILL BE DELETED AT THE END) ###
sas_download_csv_report_json_query = temp_files_dir+'/sas_download_csv_report_json_query'
jira_create_new_task = temp_files_dir+'/jira-task-query.json'

####################
### SAS API DATA ###

### CHECKING SAS TOKEN EXISTS ###
if not path.isfile(sas_api_token_file):
    logging.exception('FAILED: SAS token NOT FOUND, exiting...')
    exit()

### SAVING SAS TOKEN INFO TO THE VAR ###
with open(sas_api_token_file, 'r') as f:
    sas_api_token = f.read()

### SAS API URLS AND REQUEST DATA ###
sas_project_uuid = '<your-project-uid'
sas_api_root_url = 'http://<your-server-address>/app/api/v1'
sas_api_projects_url = sas_api_root_url+'/projects'
sas_api_start_scan_url = sas_api_root_url+'/scan/start'
sas_api_last_scan_url = sas_api_projects_url+'/filtered?sort=DATE&dir=DESC&name='+sas_project_uuid+'&noScans=false&archived=false'
sas_api_download_report_url = sas_api_root_url+'/report/file'
sas_api_post_jira_task_url = sas_api_root_url+'/jira/task'

sas_query_start_scan_data = {
    'uuid': sas_project_uuid,
    'incremental': 'false'
}

sas_query_headers = {
    'Authorization': 'Bearer'+' '+sas_api_token
}

sas_query_post_headers = {
    'Authorization': 'Bearer'+' '+sas_api_token,
    'Content-Type': 'application/json'
}

proxies = {
    #'http': 'http://127.0.0.1:8080',
    #'https': 'https://127.0.0.1:8080',
    'http': None,
    'https': None
}

#####################
##### FUNCTIONS #####

##### FILES ROTATION #####

### DEFINE HOW MANY FILES TO KEEP(MOST RECENT) ###
logs_to_keep = 30
reports_to_keep = 30

def files_rotate(path_to_rotate, num_of_files_to_keep):
    count_files_to_keep = 1
    basepath = sorted(Path(path_to_rotate).iterdir(), key=path.getctime, reverse=True)
    for entry in basepath:
        if count_files_to_keep > num_of_files_to_keep:
            remove(entry)
            logging.info('removed file is: '+str(entry))
        count_files_to_keep += 1

### ESTIMATED TIME ###
def count_script_job_time():
    end_date = datetime.now()
    logging.info('Estimated time is: ' + str(end_date - today))
    exit()

#############################
##### PRE-START ACTIONS #####

logging.info('STARTED: PRE-START ACTIONS')

### CHECKING SAS DOWNLOAD CSV REPORT JSON TEMPLATE EXISTS ###
if not path.isfile(sas_download_csv_report_json_template):
    logging.exception('FAILURE: SAS Download JSON Template NOT FOUND, exiting...')
    exit()

### CREATING ALL NECESSARRY FOLDERS ###
logging.info('Starting to create all necessarry folders...')
for folder in list_of_folders:
    try:
        if mkdir(folder):
            logging.info(folder+': created')
    except FileExistsError as error:
        logging.info(folder+': exists, skipping')

logging.info('DONE: PRE-START ACTIONS\n')

##############################
### STARTING NEW SCAN JOBS ###

### STARTING NEW SAS SCAN ###
logging.info('Trying to start New Sas Scan')
try:
    sas_api_request_start_scan = requests.post(sas_api_start_scan_url, files=sas_query_start_scan_data, headers=sas_query_headers, proxies=proxies)
    sas_new_scan_start = datetime.now()
except Exception as error:
    logging.exception('FAILURE: failed to Start (POST) SAS New Scan, exiting...')
    exit()
if sas_api_request_start_scan.status_code != 200:
    logging.error('Wrong response : ' + str(sas_api_request_start_scan.status_code))
    exit()
logging.info('SUCCESS: to Start SAS New Scan')

### WRITING SCAN UUID TO VAR ###
logging.info('Trying to get & write New Sas Scan UUID to Var')
try:
    sas_scan_uuid = sas_api_request_start_scan.json()['scanUuid']
    sas_get_issues_url = sas_api_root_url+'/scans/'+sas_scan_uuid+'/vulnerabilities/filtered?severities=2&severities=3&locale=ru'
    logging.info('SAS Scan uuid = '+str(sas_scan_uuid))
except Exception as e:
    logging.exception('FAILED: to get scan_uuid, exiting')
    exit()

### WAITING FOR COMPLETE SCAN ###
logging.info('Waiting for complete scan')
logging.info('Trying to get last scan details')
try:
    sas_api_request_scan_complete = requests.get(sas_api_last_scan_url, headers=sas_query_headers, proxies=proxies)
    logging.info('SUCCESS: to get last scan details')
except Exception as error:
    logging.exception('FAILURE: to get last scan details, exiting...')
    exit()

scan_status = sas_api_request_scan_complete.json()['projects'][0]['scan']['status']

while scan_status != 'COMPLETE':
    logging.info('Scan still not completed, waiting 30 sec')
    sleep(30)
    try:
        sas_api_request_scan_complete = requests.get(sas_api_last_scan_url, headers=sas_query_headers, proxies=proxies)
    except Exception as error:
        logging.exception('FAILURE: to get last scan status, exiting...')
        exit()
    if sas_scan_uuid not in sas_api_request_start_scan.text:
        logging.error('Scan ID NOT in last scan list, exiting')
        exit()
    scan_status = sas_api_request_scan_complete.json()['projects'][0]['scan']['status']
    if scan_status == 'ERROR':
        logging.error('Scan Status is ERROR, exiting')
        exit()

logging.info('SUCCESS: Scan status is COMPLETE')

sas_new_scan_end = datetime.now()
logging.info(f'Scan time is: {str(sas_new_scan_end - sas_new_scan_start)}\n')

####################################
### PREPARING SCAN REPORT  QUERY ###
logging.info('Trying preparing scan report query')

### PREPARE QUERY TO DOWNLOAD SCAN REPORT ###
logging.info('Preparing query to download scan report')
try:
    with open(sas_download_csv_report_json_template, 'r', encoding='utf_8_sig') as reader, open(sas_download_csv_report_json_query, 'w', encoding='utf_8_sig') as writer:
        temp_data = loads(reader.read())
        temp_data['scanUuids'][0] = sas_scan_uuid
        insert_data = dumps(temp_data, indent=4)
        writer.write(insert_data)
        writer.close()
except Exception as e:
    logging.exception('FAILED: to insert scan uuid to download report query, exiting')
    exit()
logging.info('SUCCEEDED: to insert scan uuid to download report query')

### GETTING SCAN'S ISSUES(MEDIUM & CRITICAL) ###
logging.info('Trying to get issues of new scan')

try:
    sas_get_issues_request = requests.get(sas_get_issues_url, headers=sas_query_headers, proxies=proxies)
    if sas_get_issues_request.status_code == 200:
        logging.info('SUCCEEDED: to get issues of new scan')
        sas_issues_ids_list = []
        for index in range (len(sas_get_issues_request.json())):
            for key in sas_get_issues_request.json()[index]:
                if key != 'issues':
                    continue
                for issue in sas_get_issues_request.json()[index][key]:
                    sas_issues_ids_list.append(issue)
    else:
        logging.exception('FAILED: to get issues of new scan, exiting...')
        exit()    
except Exception as e:
    logging.exception('FAILED: to get issues of new scan, exiting...')
    exit()

logging.info('SUCCEEDED: to get issues of new scan\n')

#########################################
### GETTING AND PARSING SCAN REPORT ###
logging.info('Trying to get and parse scan report')

### GETTING SCAN REPORT ZIP ###
logging.info('Trying to get scan report archive')
try:
    sas_api_download_report_request = requests.post(sas_api_download_report_url, data=open(sas_download_csv_report_json_query, 'rb'), headers=sas_query_post_headers, proxies=proxies)
    with open(sas_report_zip, 'wb') as f:
        f.write(sas_api_download_report_request.content)
except Exception as e:
    logging.exception('FAILED: Trying to get scan report archive, exiting')
    exit()
logging.info('SUCCEEDED: to get scan report archive')

### FINDING & EXTRACTING PROPER(DETAILED_RESULTS) REPORT IN ZIP ###
logging.info('Trying to check proper report in zip file')
try:
    with ZipFile(sas_report_zip, 'r') as archive:
        count_proper_report = 0
        for member in archive.namelist():
            filename = path.basename(member)
            if filename == 'Detailed_Results.csv':
                count_proper_report += 1
                source = archive.open(member)
                target = open(path.join(temp_files_dir, filename), 'wb')
                with source, target:
                    shutil.copyfileobj(source, target)
                    proper_report_path = temp_files_dir+'/Detailed_Results.csv'
                    break
        if count_proper_report == 0:
            logging.exception('FAILED: to find and proper report in zip file')
            exit()
        logging.info('SUCCEEDED: to find and extract proper report in zip file')
except Exception as error:
    logging.exception('FAILED: to find and extract proper report in zip file')

### PARSE PROPER REPORT ###
logging.info('Trying to parse proper report csv')
try:
    report_data = read_csv(proper_report_path)
    df = DataFrame(report_data, columns=['Уязвимость', 'Язык', 'Описание', 'Рекомендации', 'Ссылки', 'Название файла', 'Номер строки', 'Уровень критичности', 'Статус', 'Идентификатор задачи в Jira'])
    logging.info('SUCCEED: to parse proper report csv')
except Exception as e:
    logging.exception('FAILED: to parse proper report csv, exiting')
    exit()

### CHECK IF ISSUES INDEX NOT EQUAL REPORT INDEXES ###
logging.info('Checking if not equal indexes for issues list and report data')
if len(sas_issues_ids_list) != len(df):
    logging.error('FAILED: not equal indexes for issues list and report data, exiting...')
    exit()
logging.info('SUCCEEDED: Checking if not equal indexes for issues list and report data\n')

###########################
### CREATING JIRA TASKS ###

logging.info('Starting create Jira tasks jobs')

### CREATED JIRA TASKS LIST ###
created_jira_tasks = []

### CREATE VARS FOR NEW JIRA TASK(S) ###
logging.info('Trying to create vars for new jira tasks\n')
for index in df.index:
    Sas_Jira_id = str(df['Идентификатор задачи в Jira'][index])
    ### CHECK TASKA ARE ALREADY CREATED(SKIP) ###
    if len(Sas_Jira_id) > 1:
        logging.info(f'Jira task is already exist: {Sas_Jira_id}, skipping\n')
        continue
    Sas_Vuln = str(df['Уязвимость'][index])
    Sas_Language = str(df['Язык'][index])
    Sas_Description = str(df['Описание'][index])
    Sas_Recomendations = str(df['Рекомендации'][index])
    Sas_Refs = str(df['Ссылки'][index]).replace(',', '\n')
    Sas_Filename = str(df['Название файла'][index])
    Sas_StringNum = str(df['Номер строки'][index])
    Sas_Crit = str(df['Уровень критичности'][index])
    Sas_Status = str(df['Статус'][index])

    ### ENCAPSULATE SAS REPORT VARS TO NEW JITA TASK QUERY ###
    logging.info('Starting to encapsulate CSV report data to JIRA TASK query...')
    try:
        with open(jira_task_template, 'r', encoding='utf_8_sig') as reader, open(jira_create_new_task, 'w', encoding='utf_8_sig') as writer:
            temp_data = loads(reader.read())
            temp_data['summary'] = Sas_Vuln
            temp_data['description'] = '*Язык*:\n'+Sas_Language+'\n\n'+'*Описание уязвимости*:\n'+Sas_Description+'\n\n*Название файла:*\n'+Sas_Filename+'\n\n*Номер строки:*\n'+Sas_StringNum+'\n\n*Ссылки*:\n'+Sas_Refs
            if Sas_Crit == 'Критический':
                temp_data['priority'] = 3
            elif Sas_Crit == 'Средний':
                temp_data['priority'] = 2
            elif Sas_Crit == 'Низкий':
                temp_data['priority'] = 1
            elif Sas_Crit == 'Информационный':
                temp_data['priority'] = 0
            temp_data['issue'] = sas_issues_ids_list[index]
            insert_data = dumps(temp_data, indent=4)
            writer.write(insert_data)
            writer.close()

            ### SEND JSON QUERY TO JIRA API ###
            logging.info('Sending JSON data to Jira API...')
            try:
                jira_api_request = requests.post(sas_api_post_jira_task_url, data=open(jira_create_new_task, 'rb'), headers=sas_query_post_headers)
                if jira_api_request.status_code != 200:
                    logging.error('FAILED: status code not 200, exiting...')
                    logging.info(str(jira_api_request.status_code))
                    logging.info(str(jira_api_request.text))
                    exit()
                logging.info('JIRA TASK CREATED: '+str(jira_api_request.json()['taskKey']))
            except Exception as error:
                logging.exception('FAILED: to create Jira task via Sas API, exiting...')
                exit()
    except Exception as error:
        logging.exception(
            'FAILED: Failed to encapsulate modified CSV report data to JIRA query, exiting...')
        exit()
if len(created_jira_tasks) == 0:
    logging.info('NO JIRA TICKETS CREATED(EVERYTHING IS CREATED ALREADY)!')

logging.info(f'Created JIRA Tasks List is:\n{created_jira_tasks}\n')

#####################
##### POST JOBS #####

logging.info('STARTED: POST JOBS')

logging.info('Writing processed report ID to processed reports check list...')

#logging.info('Removing all temporary files:')
#try:
#    logging.info('Removing temporary jira_create_new_task query...')
#    remove(jira_create_new_task)
#    logging.info('Removing  temporary download report query...')
#    remove(sas_download_csv_report_json_query)
#    logging.info('Removing  temporary report file...')
#    remove(proper_report_path)
#except Exception as error:
#    logging.exception(
#        'Failed all/some temporary files...\n')

logging.info('STARTING FILES ROTATION...')
logging.info('Starting log rotation...')
try:
    files_rotate(logs_dir, logs_to_keep)
except Exception as error:
    logging.exception('FAILURE: failed to rotate logs')
logging.info('Finished log rotation\n')    
logging.info('Starting SAS reports rotation...')
try:
    files_rotate(sas_reports, reports_to_keep)
except Exception as error:
    logging.exception('FAILURE: failed to rotate reports')
logging.info('Finished reports rotation')    
logging.info('Finished Files Rotation\n')

logging.info('DONE: POST JOBS\n')

logging.info('SUCCEEDED: Script job done!') 
count_script_job_time()  
