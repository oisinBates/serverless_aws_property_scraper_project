from __future__ import print_function
from bs4 import BeautifulSoup
import requests
import boto3
import botocore
import json
# from selenium import webdriver


def handler(event, context):
	s3 = boto3.client('s3')

	#get existing json for updating with up-to-rental listings
	rent_json_url = "http://cheapdublinrent.guru/dublin1.json"
	rent_json_response = requests.get(rent_json_url)
	rent_json_formatted =  rent_json_response.json()

	#get rental listings
	page = requests.get("http://www.rent.ie/rooms-to-rent/renting_dublin/dublin-city-centre/room-type_either/sort-by_price_up/")
	soup = BeautifulSoup(page.content, 'html.parser')


	# #Experimenting with Selenium
	# driver = webdriver.Firefox(executable_path='/home/oisin/cheapdublinrent/cheapdublinrent_scraper/geckodriver')
	# driver.set_page_load_timeout(10)
	# driver.get("http://www.rent.ie/rooms-to-rent/renting_dublin/dublin-city-centre/room-type_either/sort-by_price_up/")
	# soup = BeautifulSoup(driver.page_source, 'html.parser')
	# https://stackoverflow.com/questions/31482395/page-request-not-loading-fully
	# https://stackoverflow.com/questions/40208051/selenium-using-python-geckodriver-executable-needs-to-be-in-path

	count=1
	# parse data from property site
	for link in soup.find_all("div", class_="search_result"):
		if(count<=9):
			key = str(count)

			rent_json_formatted[str(count)]['name'] = link.a.string.strip()
			rent_json_formatted[key]['url'] = link.a['href']
			rent_json_formatted[key]['imgSrc'] = link.find("img", class_="sresult_thumb")['src']
			Image_Blurb = link.find("div", class_="sresult_description")

			price_string = Image_Blurb.strong.string
			price_array = price_string.split(" ")
			price = price_array[0]
			price = int(price[1:])
			price_frequency_string ="per month"
			price_frequency = price_array[1]
			if(price_frequency == "weekly"):
				price = (price*52)/12
				price_frequency_string = "per month (approx.)"

			rent_json_formatted[key]['price'] = price
			rent_json_formatted[key]['frequency'] = price_frequency_string

			Image_Blurb = Image_Blurb.br.next_sibling.strip()
			Image_Blurb = ' '.join(Image_Blurb.split())
			print("Image_Blurb", Image_Blurb)
			rent_json_formatted[key]['description'] = Image_Blurb

			count=count+1
		else:
			break


	# #encode json dictionary
	rent_json_encoded = json.dumps(rent_json_formatted)
	#upload to aws S3
	s3.put_object(
		Body=rent_json_encoded,
		Bucket='cheapdublinrent.guru',
		Key='dublin1.json',
	)
