# coding: utf-8
# --------------------------------------------------------
#    __init__ - BAG geocoder init file
#
#    creation date        : 12 December 2014
#    copyright            : (c) 2013 by Eelke Jager
#    e-Mail               : info [at] lytrix.com
#
#	This plugin is partly based on the framework of the 
#	MMQGIS Geocode CSV with Google plugin created by Michael Minn. 
#	Go to http://plugins.qgis.org/plugins/mmqgis/ for more information.
#	
#	The geocoding is provided by the www.pdok.nl geocoding webservice:
#	Go to https://www.pdok.nl/nl/service/openls-bag-geocodeerservice 
#	for more information.
#
#   The BAG geocoder is free software and is offered without guarantee
#   or warranty. You can redistribute it and/or modify it 
#   under the terms of version 2 of the GNU General Public 
#   License (GPL v2) as published by the Free Software 
#   Foundation (www.gnu.org).
# --------------------------------------------------------

import csv
import sys
from sys import argv
import urllib
import os.path
import urllib2
import re
import codecs
from xml.dom import minidom
from xml.dom.minidom import parseString
from math import *

# --------------------------------------------------------------
#    BAG_geocode_pdok - Geocode CSV points from Pdok
# --------------------------------------------------------------

# set argument from_file for file loading statement after script name
script, from_file = argv

# --------------------------------------------------------------
#   Functions
# --------------------------------------------------------------

def RD2WGS84(X, Y):
	# downloaded from http://forum.geocaching.nl/index.php?showtopic=7886
	
	dX = (X - 155000) * 10 ** -5
	dY = (Y - 463000) * 10 ** -5
	
	SomN = (3235.65389 * dY) + (-32.58297 * dX ** 2) + (-0.2475 * dY ** 2) + (-0.84978 * dX ** 2 * dY) + (-0.0655 * dY ** 3) + (-0.01709 * dX ** 2 * dY ** 2) + (-0.00738 * dX) + (0.0053 * dX ** 4) + (-0.00039 * dX ** 2 * dY ** 3) + (0.00033 * dX ** 4 * dY) + (-0.00012 * dX * dY)
	SomE = (5260.52916 * dX) + (105.94684 * dX * dY) + (2.45656 * dX * dY ** 2) + (-0.81885 * dX ** 3) + (0.05594 * dX * dY ** 3) + (-0.05607 * dX ** 3 * dY) + (0.01199 * dY) + (-0.00256 * dX ** 3 * dY ** 2) + (0.00128 * dX * dY ** 4) + (0.00022 * dY ** 2) + (-0.00022 * dX ** 2) + (0.00026 * dX ** 5)

	Latitude = 52.15517 + (SomN / 3600)
	Longitude = 5.387206 + (SomE / 3600)

	LatitudeGraden = Latitude
	LongitudeGraden = Longitude

	LatitudeMinuten = (Latitude - LatitudeGraden) * 60.0
	LongitudeMinuten = (Longitude - LongitudeGraden) * 60.0

	Latitude = '%s' % (LatitudeGraden)
	Longitude = '%s' % (LongitudeGraden)

	return Latitude, Longitude

def getXMLpdok(addressLine):
	# add %20 for correct white'pace handling, else you get no hit
	addressLine = re.sub(r'\'','%27',addressLine)
	addressLine = re.sub(r'\’','%27',addressLine)
	addressLine = re.sub(r'\s','%20',addressLine)
	
	# run get XML statement
	url = "http://geodata.nationaalgeoregister.nl/geocoder/Geocoder?zoekterm=" + addressLine

	print 'get xml: %s' % url
	xml = urllib2.urlopen(url).read()
	doc = parseString(xml)

	# create exceptions in case there is no value present and still get a proper output written
	try:
		correctAddress = doc.getElementsByTagName("xls:Street")[0].firstChild.nodeValue
	except:
		correctAddress = ''
	try:
		correctPostalcode = doc.getElementsByTagName("xls:PostalCode")[0].firstChild.nodeValue
	except:
		correctPostalcode = ''
	try:
		correctBuildingnumber = doc.getElementsByTagName("xls:Building")[0].getAttribute('number')
		print correctBuildingnumber
	except:
		correctBuildingnumber = ''
	try:
		correctSubdivision = doc.getElementsByTagName("xls:Building")[0].getAttribute('subdivision')
	except:
		correctSubdivision = ''
	return doc, correctAddress, correctBuildingnumber, correctSubdivision, correctPostalcode, url

def GetXYLatLonandWriteRow():
	if xmlTag:	
		remark=True
		# split X and Y coordinate in list
		XY = xmlTag.split()
		if XY:
			X = float(XY[0])
			Y = float(XY[1])
			# reproject to wgs84
			Latitude, Longitude = RD2WGS84(X, Y)
			print "x: %s" % X
			print "y: %s" % Y
			print "Lat: %s" % Latitude
			print "Lon: %s" % Longitude
			# add BAG fields and XY + LatLon values as extension to the csv file for each row
			row.extend([correctAddress, correctBuildingnumber, correctSubdivision, correctPostalcode,X,Y,Latitude,Longitude])
			print row
			writer.writerow(row)	

# --------------------------------------------------------------
#  Read the CSV file header
# --------------------------------------------------------------

infile = open(from_file, 'r')
dialect = csv.Sniffer().sniff(infile.readline(), [',',';',';','|'],)
infile.seek(0)
reader = csv.reader(infile, dialect)
header = reader.next()
print header	
header.extend(['BAG Straatnaam','BAG Huisnummer','BAG Toevoeging','BAG Postcode','X','Y','Latitude','Longitude'])


# --------------------------------------------------------
# Create empty files
# --------------------------------------------------------

# Create the CSV file for geocoded records
try:
	BAG_geocoded = open(os.path.splitext(from_file)[0]+'_BAG_geocoded.csv', 'w+')
except:
	print "Kan het bestand %s niet aanmaken." % BAG_geocoded		
		
writer = csv.writer(BAG_geocoded, dialect=csv.excel)
writer.writerow(header)	

# Create the CSV file for ungeocoded records
try:
	notfound = open(os.path.splitext(from_file)[0]+'_BAG_notfound.csv', 'w+')
except:
	print "Kan het bestand %s niet aanmaken." % notfoundfile		

notwriter = csv.writer(notfound, dialect=csv.excel)
notwriter.writerow(header)			
notfound_list=[]

# Start counters at zero
recordcount = 0
notfoundcount = 0

# --------------------------------------------------------
# SET DICTIONARIES
# --------------------------------------------------------

# checklist for header name to do address geocoding on:

headernameschecker =[['adres','straat','adressen','address','straatnaam','straatnamen','straten','locatie','locaties'],
# checklist for header name to do city name geocoding on:
['huisnummer','nummer','huisnummers','buildingnumber','number'],
# checklist for header name to do city name geocoding on:
['toevoeging','toev','toev.','niveau','huisnummertoevoeging'],
['letter','huisletter','huislettertoevoeging'],
# checklist for header name to do city name geocoding on:
['plaats','woonplaats','stad','steden','city','place','vestigingsplaats'],
# checklist for header name to get postal codes:
['postcode','pc6','pc','postal code']]

# --------------------------------------------------------
# find column header id's to match for cleanup
# --------------------------------------------------------

addresscol = ''
numbercol = ''
levelcol = ''
lettercol = ''
citycol = ''
postalcodecol = ''

for i in range(0, len(header)):
	try:
		if header[i].lower() in headernameschecker[0]:
			addresscol = i
			print addresscol
			print 'column found named: %s' % header[i]
		if header[i].lower() in headernameschecker[1]:
			numbercol = i
			print numbercol
			print 'column found named: %s' % header[i]
		if header[i].lower() in headernameschecker[2]:
			levelcol = i
			print 'column found named: %s' % header[i]
		if header[i].lower() in headernameschecker[3]:
			lettercol = i
			print 'column found named: %s' % header[i]
		if header[i].lower() in headernameschecker[4]:
			citycol = i
			print citycol
			print 'column found named: %s' % header[i]
		if header[i].lower() in headernameschecker[5]	:	
			postalcodecol = i
			print 'column found named: %s' % header[i]		
	except:
		print 'no column name found named: %s' % x
		
# --------------------------------------------------------
# loop through each row in csv file
# --------------------------------------------------------
for row in reader:	

	# check which columns are found and generate a generic address line
	if lettercol is '' and numbercol and levelcol:
		print 'lettercol is none and numbercol and levelcol'
		# for each column do...
		line ='%s %s %s' % (row[addresscol],row[numbercol],row[levelcol])
		print 'found line: %s' % line
	elif levelcol is '' and numbercol:
		print 'levelcol is none and numbercol'
		# for each column do...
		line ='%s %s' % (row[addresscol],row[numbercol])
		print 'found line: %s' % line
	else:
		print 'just one addressline'
		# for each column do...
		line ='%s' % row[addresscol]
		print 'found line: %s' % line

	recordcount += 1	

	# --------------------------------------------------------
	# Do A Basic Cleanup For Each Cell Type
	# --------------------------------------------------------

	# remove ,
	line = re.sub(r',', '', line, re.M|re.I)	
	# remove everything between () including the brackets
	line = re.sub(r'\(.*\)', '', line, re.M|re.I)
	# remove near or across words
	line = re.sub(r'tegenover|nabij|t/o|bij|vlakbij|supermarkt|ah\b', '', line, re.M|re.I)
	# remove everything between () including the brackets
	line = re.sub(r'(unit|kamer|afdeling)(\s+.*\b)', '', line, re.M|re.I)
	# replace v. for van
	line = re.sub(r'v\.', 'van', line, re.M|re.I)
	# remove space between postal code
	line = re.sub(r'(\d{4})(\s+)([A-Z]{2})', r'\1\3', line)
	# rename al writing styles of House to H
	line = re.sub(r'(\s+|-)(hs|HS|huis|Huis|bg|BG|"begane grond")','H', line)
	# rename al writing styles of BIS to BS
	line = re.sub(r'(?=\s+|-)BIS\s|Bis\s|bis','BS', line)
	# remove hg, hoog, etage
	line = re.sub(r'(?!\d+)([\s-]*)hg|hoog|etage\b','', line)
	# replaced roman subdivision with numbers
	line = re.sub(r'(?!\d+)([\s-]*)III|iii\b',' 3', line)
	line = re.sub(r'(?!\d+)([\s-]*)II|ii',' 2', line)
	line = re.sub(r'(?!\d+)([\s-]*)I|i\b',' 1', line)
	line = re.sub(r'(?!\d+)([\s-]*)rood|Rood','RDA', line)
	line = re.sub(r'(?!\d+)([\s-]*)rood|Zwart','ZWA', line)
	# rename str to straat where it stands on the end a word and continues by a whitespace
	line = re.sub(r'(?=\w+)str(?=\s|\.)','straat',line)
	# rename ln to laan where it stands on the end a word and continues by a whitespace
	line = re.sub(r'(?=\w+)ln(?=\s|\.)','laan',line)
	line = re.sub(r'^pr(?=\s|\.)','prins',line)	
	# rename str to straat where it stands on the end a word and continues by a whitespace
	line = re.sub(r'\bAdm|adm(\.|\s*)(?!\w+)','admiraal ',line)	
	# remove everything between () including the brackets
	line = re.sub(r'\s{1,5}', ' ', line, re.M|re.I)
	# remove weird characters
	line = re.sub(r'\.+','',line)
	print 'cleaned up line: %s' % line

	# select all words before digits or select all for address
	searchAddress = re.match( r'(^.*?(?=(\s+\d+)))', line, re.M|re.I)
	# select only complete postal codes 1000AA or 1000 AA
	searchPostalcode = re.search( r'(\d{4}\w{2})', line, re.M|re.I)
	# select numbers not a postal code starting with a whitespace
	searchHousenumber= re.search( r'((?!\d{4}\w{2})\s+(\d+))', line, re.M|re.I)
	# find first letter after() word + whitespace + number) (whitepace or -)(only a number H with max 2 numbers and forms a complete word)
	searchHouselevel= re.search( r'([a-zA-Z]+\s+\d+)(\s|-)(\d+\b)', line, re.M|re.I)
	# find first letter after() word + whitespace + number) (whitepace or -)(only a letter not consisting of H with max 2 numbers and forms a complete word)
	searchHouseletter= re.search( r'([a-zA-Z]+\s+\d+)(\s*|-)([a-zA-Z]{1,3}\b)', line, re.M|re.I)

	# set normalized address fields
	addressname = ""
	number = ""
	level = ""
	letter = ""
	postalcode = ""
	city = '+%s' % row[citycol].strip() 
	# remove province additions to get a proper result back
	city = re.sub(r'(\s+)(DR|Drenthe|FL|Flevoland|FR|Friesland|GD|Gelderland|GR|Groningen|LB|Limburg|NB|Noord-Brabant|NH|Noord-Holland|OV|Overijssel|UT|Utrecht|ZH|Zuid-Holland|ZL|Zeeland)','', city)
	print 'city cleaned Province name: %s' % city
	
	if searchAddress:
		addressname = '%s' % searchAddress.group().strip()
		print "search --> searchAddress.group() : ", addressname
	if not searchAddress and not searchPostalcode:
		addressname = '%s' % line
	if searchHousenumber:
		number = '+%s' % searchHousenumber.group().strip()
		print "search --> searchHousenumber.group() : ", number
	if searchHouselevel:
		level = '+%s' % searchHouselevel.group(3).strip()
		print "search --> searchHouselevel.group(3) : ", level
	if searchHouseletter:
	 	letter = '%s' % searchHouseletter.group(3).strip()
	 	print "search --> searchHouseletter.group(3) : ", letter
 	if searchPostalcode:
		postalcode = '+%s' % searchPostalcode.group().strip()
		print "search --> searchPostalcode.group() : ", postalcode
	else:
		print "Nothing found"

	# --------------------------------------------------------
	# build up the address with convention for api pdok.nl
	# -------------------------------------------------------- 	
	
	if addressname is not "":
		if number is not '':
			# run this addres line if there is a number field
			total_address = addressname+number+level+letter+city
		else:
			# run this address line if there is no house number found, it is probably a postal code or only an address:
			total_address = line+city
			print 'total_address= %s' % line 	
	
		try:
			print 'Running first xml retrieval: addressname+number+level+letter+city'
			# get all the values back from the xml
			doc, correctAddress, correctBuildingnumber, correctSubdivision, correctPostalcode, url = getXMLpdok(total_address)
			print 'inserted address:', addressname.lower()
			print 'pdok address    :', correctAddress.lower()
			if (addressname.lower().strip() == correctAddress.lower().strip() or re.sub('y','ij',addressname.lower().strip()) == correctAddress.lower().strip() or re.sub('ij','y',addressname.lower().strip()) == correctAddress.lower().strip()):
				xmlTag = doc.getElementsByTagName("gml:pos")[0].firstChild.nodeValue
				GetXYLatLonandWriteRow()
			
			# if total_address is not correctly written do...
			if (addressname.lower().strip() != correctAddress.lower().strip() and addressname is not None):
				# this is a dictionary where the words are replaced,
				replacewords = [
				# replace 1e and bis
				[[r'1e|1ste', 'Eerste'],['2ste','Tweede'],['3ste','Tweede'],['BS',''],['BSA','A'],['BSB','B'],['BSC','C'],['BSD','D']],
				# add an extra s, replace y's and transform back if there is no hit
				[['straat','sstraat']],[['ij','y']],[['y','ij']],[['y','ij'],['sstraat','straat']],
				[['straat','weg'],['weg','straat'],[r'[y]','ij']],
				# if pr. has no hit the prins was added, if this still has no hit, replace for prinses
				[[r'[prins]','prinses']]]				

				print "if address name is mismatch run first cleanup, correct address writing from '1e' to 'Eerste' for example"
				try:
					if (addressname.lower().strip() != correctAddress.lower().strip()):
						# loop for each wordset in dictionary replacewords
						for words in replacewords:
							# loop through each word
							for i in range(len(words)):
								print '%s' % words
								m = re.match(words[i][0], addressname)
								print m
								if m: 
									addressname = re.sub(words[i][0],words[i][1],addressname, re.M|re.I)
									print addressname
									total_address = addressname+number+level+letter+city
									# return
									doc, correctAddress, correctBuildingnumber, correctSubdivision, correctPostalcode, url = getXMLpdok(total_address)
									print 'inserted address:', addressname
									print 'pdok address    :', correctAddress
							
									if (addressname.lower().strip() == correctAddress.lower().strip() or re.sub('y','ij',addressname.lower().strip()) == correctAddress.lower().strip() or re.sub('ij','y',addressname.lower().strip()) == correctAddress.lower().strip()):
										xmlTag = doc.getElementsByTagName("gml:pos")[0].firstChild.nodeValue
										GetXYLatLonandWriteRow()
										break		
					if (addressname.lower().strip() != correctAddress.lower().strip()):
						print 'Running third cleanup: erase 1 digit from the building number'
						number_minus_1char_left=number[0:len(str(number))-1]
						print 'origional number: %s' % len(str(number))
						print 'number shortened by 1: %s' % number_minus_1char_left
						total_address = addressname+number_minus_1char_left+city
						doc, correctAddress, correctBuildingnumber, correctSubdivision, correctPostalcode, url = getXMLpdok(total_address)
						print 'inserted address:', addressname
						print 'pdok address    :', correctAddress
						if (addressname.lower().strip() == correctAddress.lower().strip()):
							xmlTag = doc.getElementsByTagName("gml:pos")[0].firstChild.nodeValue								
							GetXYLatLonandWriteRow()

				except:
					# else just try to write the response anyway because the matching could be okay
					xmlTag = doc.getElementsByTagName("gml:pos")[0].firstChild.nodeValue								
					GetXYLatLonandWriteRow()
		except:
			# if there is no match, write the row to the notfound csv
			notfoundcount += 1
			notwriter.writerow(row)
			#notfound_list.append(url)
	else:
		# if there is no number value found, assume it is a postal code, so do this:
		total_address = postalcode+city
		print total_address
		doc, correctAddress, correctBuildingnumber, correctSubdivision, correctPostalcode, url = getXMLpdok(total_address)
		xmlTag = doc.getElementsByTagName("gml:pos")[0].firstChild.nodeValue
		GetXYLatLonandWriteRow()
