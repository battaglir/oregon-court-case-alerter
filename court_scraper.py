# %% [markdown]
# Oregon Case filing alerter
# 
# Scrapes specific cases in Oregon circuit court to alert when new filings are made.
# 
# 

# %%
# request the required databases
import requests, time, datetime, os, pytz, re, random
from bs4 import BeautifulSoup
from slack_sdk import WebClient

#Set this variable to False. If new filings are found, it will be sent to true and we won't send the "no new filings found" message to Slack.
NewInfo = False

#Setup a session so we can keep the cookies for the next request
s = requests.Session()
pacific_tz = pytz.timezone('US/Pacific')
#Get the login information from the environment variables
login_username = os.environ.get('LOGIN_USERNAME')
login_password = os.environ.get('LOGIN_PASSWORD')
SLACK_TOKEN = os.environ.get("SLACK_TOKEN")

#define custom headers
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36'
}

#Setup the POST request including the login information
payload = {'UserName': login_username, 'Password': login_password, 'ValidateUser': '1', 'dbKeyAuth': 'JusticePA', 'SignOn': 'Sign+On'}

#Send the POST request
r = s.post('https://publicaccess.courts.oregon.gov/PublicAccessLogin/Login.aspx?ReturnUrl=%2fPublicAccessLogin%2fdefault.aspx', data=payload, headers=headers)

r.raise_for_status()

# %%
#This section does one search for Jackson County, but all it's doing is getting us a __VIEWSTATE and __EVENTVALIDATION code that we can use to send the next request

#Define the URL for the search
county_url = 'https://publicaccess.courts.oregon.gov/PublicAccessLogin/Search.aspx?ID=200'

#Define the POST request for the search
county_data = {
	'NodeID': '101100',
	'NodeDesc': 'Jackson'
}

#Send the POST request
results = s.post(county_url, data=county_data, headers=headers, cookies=s.cookies)

# Wait for a random amount of time between 1 and 2 seconds
time.sleep(random.uniform(1, 2))

results.raise_for_status()

# %%

# Parse the HTML content of results
soup = BeautifulSoup(results.text, 'html.parser')

# Find the input element with the name '__VIEWSTATE'
viewstate = soup.find('input', {'name': '__VIEWSTATE'})['value']

# Find the input elements with the names '__VIEWSTATEGENERATOR' and '__EVENTVALIDATION'
viewgen = soup.find('input', {'name': '__VIEWSTATEGENERATOR'})['value']
eventval = soup.find('input', {'name': '__EVENTVALIDATION'})['value']

# %%
#Set the current date in the format MM/DD/YYYY
current_date = datetime.datetime.now(tz=pacific_tz).strftime("%m/%d/%Y")
print(f"Current date: "+current_date)

#Open the tracked_cases.txt file and read the case numbers into a list
with open("tracked_cases.txt", 'r') as f:
	tracked_cases = [line.strip() for line in f.readlines()]
      
print(f"Tracked cases: {tracked_cases}")

#Set the POST request to search for all cases filed today in all counties.
for CASE_NUMBER in tracked_cases:
	print(f"Searching for case number: {CASE_NUMBER}")
	search_data = {
		"__EVENTTARGET": "",
		"__EVENTARGUMENT": "",
		"__VIEWSTATE": viewstate,
		"__VIEWSTATEGENERATOR": viewgen,
		"__EVENTVALIDATION": eventval,
		"NodeID": "101100,102100,103100,104100,104210,104215,104220,104225,104310,104320,104330,104410,104420,104430,104440,105100,106100,106200,106210,107100,107200,107300,107400,107500,108100,109100,110100,110200,111100,112100,113100,114100,115100,115200,116100,117100,118100,119100,120100,121100,122100,122200,123100,124100,124200,125100,126100,127100,150000,150100,150200",
		"NodeDesc": "All+Locations",
		"SearchBy": "0",
		"ExactName": "on",
		"CaseSearchMode": "CaseNumber",
		"CaseSearchValue": CASE_NUMBER,
		"CitationSearchValue": "",
		"CourtCaseSearchValue": "",
		"PartySearchMode": "Name",
		"AttorneySearchMode": "Name",
		"LastName": "",
		"FirstName": "",
		"cboState": "AA",
		"MiddleName": "",
		"DateOfBirth": "",
		"DriverLicNum": "",
		"CaseStatusType": "0",
		"DateFiledOnAfter": "",
		"DateFiledOnBefore": "",
		"chkCriminal": "on",
		"chkFamily": "on",
		"chkCivil": "on",
		"chkProbate": "on",
		"chkDtRangeCriminal": "on",
		"chkDtRangeFamily": "on",
		"chkDtRangeCivil": "on",
		"chkDtRangeProbate": "on",
		"chkCriminalMagist": "on",
		"chkFamilyMagist": "on",
		"chkCivilMagist": "on",
		"chkProbateMagist": "on",
		"DateSettingOnAfter": "",
		"DateSettingOnBefore": "",
		"SortBy": "fileddate",
		"SearchSubmit": "Search",
		"SearchType": "CASE",
		"SearchMode": "CASENUMBER",
		"NameTypeKy": "",
		"BaseConnKy": "",
		"StatusType": "true",
		"ShowInactive": "",
		"AllStatusTypes": "true",
		"CaseCategories": "",
		"RequireFirstName": "",
		"CaseTypeIDs": "",
		"HearingTypeIDs": "",
	}

	# Wait for a random amount of time between 1 and 2 seconds
	time.sleep(random.uniform(1, 2))

	#Send the POST request to search for all cases filed today in all counties.
	results = s.post(county_url, data=search_data, headers=headers, cookies=s.cookies)

	results.raise_for_status()

	# %%
	#Parse the HTML content of results
	soup = BeautifulSoup(results.text, 'html.parser')

	#Find the case URL in here. This is the link to the case detail page.
	case_id = soup.find("a", href=re.compile(r"CaseDetail\.aspx\?CaseID=\d+"))["href"]

	#Set the case URL to the full URL for the case detail page.
	case_url = "https://publicaccess.courts.oregon.gov/PublicAccessLogin/" + case_id

	#Now we reset the results variable to the case detail page and parse it for the court filings.
	results = s.get(case_url, headers=headers, cookies=s.cookies)

	results.raise_for_status()
	
	#create a new BeautifulSoup object with the case detail page
	soup = BeautifulSoup(results.text, features="html.parser")

	#Empty out the event_list
	event_list = []

	#Find the table of court filings
	main_table = soup.find(id="COtherEventsAndHearings")

	#find the parent row of that caption
	tr = main_table.find_parent("tr")

	#find the parent table of that row
	tbody = tr.find_parent("table")

	for row in tbody.find_all('tr'):
		#If the row has a bold tag, it's a header of a court filing and we want it.
		if row.b:
			event = row.b.get_text(strip=True)
			event_list.append(event)

	#Check if a master list already exists for this case.
	if os.path.exists(f"cases/{CASE_NUMBER}_master.txt"):
		#Open up the master list and read it into a list
		with open(f"cases/{CASE_NUMBER}_master.txt", 'r') as f:
			master_events = f.read().splitlines()
		#Check if the new list of events matches the master list.
		if set(event_list) != set(master_events):
			#Set NewInfo to True so we don't send the "no new filings found" message to Slack.
			NewInfo = True
			#Pull out the new events that are not in the master list and write them to the master list.
			new_events = [event for event in event_list if event not in master_events]
			#Write the new events to the master list
			with open(f"cases/{CASE_NUMBER}_master.txt", 'w') as f:
				for event in event_list:
					f.write(f"{event}\n")
			print(f"New events found: {', '.join(new_events)}")

			#Here we will add a slack message to alert us of the new filings.
			client = WebClient(token=SLACK_TOKEN)
	
			clean_date = datetime.datetime.now(tz=pacific_tz).strftime("%B %d, %Y")
			#Post the message to the Slack channel
			client.chat_postMessage(
				channel="C07QGTYJJ9Z",
				text="New filings found in " + CASE_NUMBER + ", " + clean_date + "\n" + "\n".join(new_events) + "\n-------------------------"
			)

		else:
			print("No new events found.")
		continue

	else:
		#If no master list exists, create one.
		with open(f"cases/{CASE_NUMBER}_master.txt", 'w') as f:
			for event in event_list:
				f.write(f"{event}\n")
		print(f"No master file exists for {CASE_NUMBER}. Created new master file.")
		continue

#If we found no new events across all cases, send a slack message anyways sayng so.
if NewInfo == False:
	print("No new events found for any cases.")
	#Set the Slack token from the enviromental variables

	client = WebClient(token=SLACK_TOKEN)
	
	clean_date = datetime.datetime.now(tz=pacific_tz).strftime("%B %d, %Y")
	#Post the message to the Slack channel
	client.chat_postMessage(
		channel="C07QGTYJJ9Z",
		text="No updates on tracked court cases today, " + clean_date
	)