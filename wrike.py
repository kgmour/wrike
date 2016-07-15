import requests
import csv
import ConfigParser
import json
import urllib
import subprocess
import time


#pull in private auth credentials
config = ConfigParser.ConfigParser()
config.read('/home/kevin/Documents/python_scripts/Wrike/wrike_config.ini')
client_id = config.get('WrikeCredentials', 'client_id')
client_secret = config.get('WrikeCredentials', 'client_secret')
refresh_token = config.get('WrikeCredentials', 'refresh_token')

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
	f.write('[WrikeCredentials]\nclient_id: ' + client_id + '\nclient_secret: ' + client_secret + '\nrefresh_token: ' + new_refresh_token)

header = {'Authorization': 'bearer ' + access_token}

#Accounts
accounts_url = 'https://www.wrike.com/api/v3/accounts'
wrike_accounts_data = requests.get(accounts_url, headers=header)
wrike_accounts_data_dict = json.loads(wrike_accounts_data.text)
account_id = wrike_accounts_data_dict['data'][0]['id']


#Tasks
tasks_url = 'https://www.wrike.com/api/v3/tasks'
wrike_tasks_data = requests.get(tasks_url, headers=header)
wrike_tasks_data_dict = json.loads(wrike_tasks_data.text)

'''
#Workflows
workflows_url = 'https://www.wrike.com/api/v3/accounts/' + account_id + '/workflows'
wrike_workflows_data = requests.get(workflows_url, headers=header)
wrike_workflows_data_dict = json.loads(wrike_workflows_data.text)

#Folders
folders_url = 'https://www.wrike.com/api/v3/folders/' + task_parentId
wrike_folders_data = requests.get(folders_url, headers=header)
wrike_folders_data_dict = json.loads(wrike_folders_data.text)


wrike_tasks_data_dict['data'][0]['parentIds']
wrike_tasks_data_dict['data'][0]['createdDate']
wrike_tasks_data_dict['data'][0]['completedDate']
wrike_tasks_data_dict['data'][0]['status']
wrike_tasks_data_dict['data'][0]['title']
wrike_tasks_data_dict['data'][0]['dates']['start']
wrike_tasks_data_dict['data'][0]['dates']['due']
'''


data = []

if 'data' in wrike_tasks_data_dict:
	if 'data' not in wrike_tasks_data_dict:
		print 'All done'
	else:
		for i in wrike_tasks_data_dict['data']:
			task_row = []
			task_id = i['id']
			task = requests.get(tasks_url + '/' + task_id, headers=header)
			task_dict = json.loads(task.text)
			if 'dates' in task_dict['data'][0]:
				if 'start' in task_dict['data'][0]['dates']:
					start_date = task_dict['data'][0]['dates']['start']
					start_date = start_date[:10]
				else:
					start_date = ''
			else:
				start_date = ''
			task_parentId = task_dict['data'][0]['parentIds'][0]
			task_folder = requests.get('https://www.wrike.com/api/v3/folders/' + task_parentId, headers=header)
			task_folder_dict = json.loads(task_folder.text)
			if 'data' in task_folder_dict:
				task_workflow = task_folder_dict['data'][0]['workflowId']
			else:
				task_workflow = ''
			if 'data' in task_folder_dict:
				task_row.append(task_folder_dict['data'][0]['title'])
			else:
				task_row.append('')
			task_row.append(task_dict['data'][0]['title'])
			task_row.append(task_dict['data'][0]['status'])
			task_row.append(task_dict['data'][0]['importance'])
			task_row.append(start_date)
			if len(task_dict['data'][0]['customFields']) > 0:
				for i in task_dict['data'][0]['customFields']:
					if i['value'][:3] == '001':
						task_row.append(i.pop('value', None))
				if len(task_dict['data'][0]['customFields']) > 0:
					for i in task_dict['data'][0]['customFields'][0]:
						task_row.append(i['value'])
			data.append(task_row)
			time.sleep(.3)	





task_folder = requests.get('https://www.wrike.com/api/v3/folders/IEAAYUEXI7777777?fields=["title"]', headers=header)
