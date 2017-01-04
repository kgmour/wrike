#!/usr/bin/env python

import requests
import csv
import ConfigParser
import json
import subprocess
import time
import sys

reload(sys)
sys.setdefaultencoding('utf-8')


#pull in private auth credentials
config = ConfigParser.ConfigParser()
config.read('/home/kevin/Documents/python_scripts/Wrike/wrike_config.ini')
client_id = config.get('WrikeCredentials', 'client_id')
client_secret = config.get('WrikeCredentials', 'client_secret')
refresh_token = config.get('WrikeCredentials', 'refresh_token')
username = config.get('HadoopCredentials', 'username')
password = config.get('HadoopCredentials', 'password')
dh_url = config.get('HadoopCredentials', 'url')

refresh_params = {'client_id': client_id,
				   'client_secret': client_secret,
				   'grant_type': 'refresh_token',
				   'refresh_token': refresh_token}

#refresh token script
refresh_url = 'https://www.wrike.com/oauth2/token'
token_request = requests.post(refresh_url, data=refresh_params)
token_request_dict = json.loads(token_request.text)
new_refresh_token = token_request_dict['refresh_token']
access_token = token_request_dict['access_token']

#write new config file to update refresh_token
config_path = '/home/kevin/Documents/python_scripts/Wrike/'
with open(config_path + 'wrike_config.ini', 'w') as f:
	f.write('[WrikeCredentials]\nclient_id: ' + client_id + '\nclient_secret: ' + client_secret + '\nrefresh_token: ' + new_refresh_token +'\n\n[HadoopCredentials]\nusername: ' + username + '\npassword: ' + password + '\nurl: ' + dh_url)

header = {'Authorization': 'bearer ' + access_token}

#Accounts
accounts_url = 'https://www.wrike.com/api/v3/accounts'
wrike_accounts_data = requests.get(accounts_url, headers=header)
wrike_accounts_data_dict = json.loads(wrike_accounts_data.text)
account_id = wrike_accounts_data_dict['data'][0]['id']


#Tasks
tasks_url = 'https://www.wrike.com/api/v3/tasks?pageSize=1000'
wrike_tasks_data = requests.get(tasks_url, headers=header)
wrike_tasks_data_dict = json.loads(wrike_tasks_data.text)

#Workflows
workflows_url = 'https://www.wrike.com/api/v3/accounts/'+account_id+'/workflows'
wrike_workflows_data = requests.get(workflows_url, headers=header)
wrike_workflows_data_dict = json.loads(wrike_workflows_data.text)

column_headers = ['Folder', 'Workflow', 'Task', 'Status', 'Importance', 'Start Date', 'Due Date', 'SF Account ID']
data = []
data.append(column_headers)

next_page_token = wrike_tasks_data_dict['nextPageToken']
task_url = 'https://www.wrike.com/api/v3/tasks'
loops = 1001
run = True

while run:
	if 'data' in wrike_tasks_data_dict:
		for i in wrike_tasks_data_dict['data']:
			loops = loops - 1
			if loops == 0:
				tasks_url = 'https://www.wrike.com/api/v3/tasks?nextPageToken=' + next_page_token
				wrike_tasks_data = requests.get(tasks_url, headers=header)
				wrike_tasks_data_dict = json.loads(wrike_tasks_data.text)
				try:
					next_page_token = wrike_tasks_data_dict['nextPageToken']
				except KeyError as e:
					print e
				loops = 1000
			print loops
			task_row = []
			task_id = i['id']
			task = requests.get(task_url + '/' + task_id, headers=header)
			time.sleep(0.9)
			try:
				task_dict = json.loads(task.text)
			except ValueError as e:
				print e
				break
			if 'data' in task_dict:
				if 'dates' in task_dict['data'][0]:
					if 'start' in task_dict['data'][0]['dates']:
						start_date = task_dict['data'][0]['dates']['start'][:10]
					else:
						start_date = ''
				else:
					start_date = ''
				if 'dates' in task_dict['data'][0]:
					if 'due' in task_dict['data'][0]['dates']:
						due_date = task_dict['data'][0]['dates']['due'][:10]
					else:
						due_date = ''
				else:
					due_date = ''
				task_parentId = task_dict['data'][0]['parentIds'][0]
				task_folder = requests.get('https://www.wrike.com/api/v3/folders/' + task_parentId, headers=header)
				try:
					task_folder_dict = json.loads(task_folder.text)
				except ValueError as e:
					print e
					break
				if 'data' in task_folder_dict:
					if (task_folder_dict['data'][0]['title'] != 'Integration Services'\ 
					    and task_folder_dict['data'][0]['title'] != 'Content Services'\
					    and task_folder_dict['data'][0]['title'] != 'Security Services'\
					    and task_folder_dict['data'][0]['title'] != 'Reporting Services'\
					    and task_folder_dict['data'][0]['title'] != 'Professional Services')\
					or task_folder_dict['data'][0]['title'] == None:
						continue
					else:
						pass
				if 'data' in task_folder_dict:
					task_workflowID = task_folder_dict['data'][0]['workflowId']
					for i in wrike_workflows_data_dict['data']:
						if i['id'] == task_workflowID:
							task_row.append(i['name'])
							break
				else:
					task_row.append('')
				if 'data' in task_folder_dict:
					task_row.append(""+task_folder_dict['data'][0]['title']+"")
				else:
					task_row.append('')
				task_row.append(task_dict['data'][0]['title'])
				task_row.append(task_dict['data'][0]['status'])
				task_row.append(task_dict['data'][0]['importance'])
				task_row.append(start_date)
				task_row.append(due_date)
				if len(task_dict['data'][0]['customFields']) > 0:
					count = len(task_dict['data'][0]['customFields'])
					for i in task_dict['data'][0]['customFields']:
						if i['value'][:3] == '001':
							task_row.append(i.pop('value', None))
							del(i)
							break
						elif count == 1:
							task_row.append('')
						count = count - 1
				else:
					task_row.append('')
				data.append(task_row)
	else:
		run = False
		with open('/home/kevin/Documents/python_scripts/Wrike/wrike_data.csv', 'w') as f:
			writer = csv.writer(f, delimiter='\t')
			writer.writerows(data)
		subprocess.call('curl --user '+username+':'+password+' --data-binary "@/home/kevin/Documents/python_scripts/Wrike/wrike_data.csv" -H "Content-Type: application/octet-stream" -X PUT ' +dh_url, shell=True)
