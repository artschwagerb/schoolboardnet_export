from bs4 import BeautifulSoup
import requests

from ConfigParser import SafeConfigParser

from termcolor import colored

import os 

import sys
reload(sys)
sys.setdefaultencoding('utf8')

parser = SafeConfigParser()
parser.read('settings.ini')

current_path = os.path.dirname(os.path.realpath(__file__))

settings_download_links = True
settings_download_content = True
settings_domain = parser.get('general', 'domain')
settings_attachment_url = parser.get('general', 'attachment_url')
settings_agenda_filename = parser.get('general', 'agenda_filename')
settings_events_url = parser.get('general', 'events_url')

def get_valid_string(str):
	import string
	valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)

	return ''.join(c for c in str if c in valid_chars)

def get_events(event_list_url,get_sub_pages):
	r  = requests.get(event_list_url)

	data = r.text

	soup = BeautifulSoup(data, "html.parser")

	print "----------------------------------------------------------"
	print "Parsing Event List: %s" % (event_list_url)
	print "Checking Sub Pages: %s" % (str(get_sub_pages))
	print "----------------------------------------------------------"
	

	event_table = soup.find('table', attrs={'class':'views-table'})
	table_body = event_table.find('tbody')

	rows = table_body.find_all('tr')
	for row in rows:
		cols = row.find_all('td')
		link_url = cols[0].find('a').get('href')
		#print link_url

		get_node(settings_domain+link_url)

	if get_sub_pages:
		sub_pages = soup.find_all('li', attrs={'class':'pager-item'})

		for page in sub_pages:
			page_url = page.find('a').get('href')
			#print page_url
			get_events(settings_domain+page_url,get_sub_pages=False)
	

def get_node(node_url):
	r  = requests.get(node_url)

	data = r.text

	soup = BeautifulSoup(data, "html.parser")

	header1 = soup.find('h1')

	page_title = header1.renderContents()
	page_name = get_valid_string(page_title)
	download_dir = os.path.join(current_path,page_name)

	print "----------------------------------------------------------"
	print "Found Page: %s" % (page_title)
	print "Download Directory: %s" % (download_dir)
	print "----------------------------------------------------------"

	if not os.path.exists(download_dir):
		os.makedirs(download_dir)

	if os.path.exists(os.path.join(download_dir,"index.html")):
		os.remove(os.path.join(download_dir,"index.html"))

	if settings_download_content:
		content = soup.find('div', attrs={'class':'field-name-body'}).renderContents()
		# print content
		with open(os.path.join(download_dir,settings_agenda_filename), "wb") as file:
			file.write(content.encode('ascii','xmlcharrefreplace'))
		print colored("SUCCESS: Downloaded Page Content ",'green')

	links_div = soup.find('div', attrs={'class':'field-name-field-attachments'})

	i = 0
	if links_div and settings_download_links:
		for link in links_div.find_all('a'):
			try:
				link_url = link.get('href')
				link_text = get_valid_string(link.contents[0])

				if settings_attachment_url in link_url:
				#	print "Found: %s" % (link_url)

					download_path = os.path.join(download_dir,link_text)
					#print download_path

					if not os.path.exists(download_path):
						#print "Downloading: %s" % (link_text)
						r = requests.get(link_url, stream=True)
						if r.status_code == 200:
							with open(download_path, 'wb') as f:
								for chunk in r:
									f.write(chunk)
							print colored("SUCCESS: %s" % (link_text),'green')
						else:
							print colored("FAILURE: %s" % (link_text),'red')
					else:
						print colored("EXISTS: %s" % (link_text),'yellow')
			except:
				print colored("ERROR: %s" % (link),'red')

			i = i + 1

	print "Files: %d" % (i)


get_events(settings_events_url,get_sub_pages=True)

