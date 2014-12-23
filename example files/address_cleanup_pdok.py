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

matchfound = ''

# set index en column variables
addresscol = ''
numbercol = ''
levelcol = ''
lettercol = ''
citycol = ''
postalcodecol = ''
postalindex = ''



# search for variables in line
nonefound=0

# Start counters at zero
recordcount = 0
notfoundcount = 0

# --------------------------------------------------------------
#    BAG_geocode_pdok - Geocode CSV points from Pdok
# --------------------------------------------------------------

# set argument from_file for file loading statement after script name
script, from_file = argv



# --------------------------------------------------------------
#   Functions
# --------------------------------------------------------------
def findWholeWord(w):
	return re.compile(r'\b({0})\b'.format(w), flags=re.IGNORECASE).search


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

def getXYandLatLon():
	xmlTag=doc.getElementsByTagName("gml:pos")[indexnumbermatch].firstChild.nodeValue
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
	return X, Y, Latitude, Longitude


retrievals = 0

def getXMLpdok(addressLine):
	global matchfound 
	global doc
	global indexnumbermatch
	global level
	global letter
	indexnumbermatch = 0
	numberofrecords = 0

	# add %20 for correct white'pace handling, else you get no hit
	addressLine = re.sub(r'\'','%27',addressLine)
	addressLine = re.sub(r'\’','%27',addressLine)
	addressLine = re.sub(r'\s','%20',addressLine)
	addressLine = re.sub(r'ê','%EA',addressLine)
	
	#s = HTMLParser.HTMLParser()
	addressLine = addressLine.encode('utf-8')
	print addressLine
	url = "http://geodata.nationaalgeoregister.nl/geocoder/Geocoder?zoekterm=" + addressLine

	print 'get xml: %s' % url
	try:
		xml = urllib2.urlopen(url, timeout = 2).read()
		print 'retrieved xml...'
		doc = parseString(xml)

		#if letter=='':
		#	number_wildcard = level.upper().strip()
		#	print 'subdivision: ', number_wildcard
		#if level=='':
		number_wildcard = '%s%s' % (level.strip(), letter.upper().strip())
		print 'subdivision: ', number_wildcard

		# create exceptions in case there is no value present and still get a proper output written
		try:
			numberofrecords = doc.getElementsByTagName("xls:GeocodeResponseList")[0].getAttribute('numberOfGeocodedAddresses')
			print 'number of records',numberofrecords
		except:
			numberofrecords = 0

		if numberofrecords:
			try:
				for i in range(0,int(numberofrecords)):
					correctSubdivision = doc.getElementsByTagName("xls:Building")[i].getAttribute('subdivision')
					print correctSubdivision
					#if any(f.startswith(number_wildcnumber_wildcard) for f in correctSubdivision):		
					if number_wildcard.strip() == correctSubdivision.strip():		
						print 'It is a match on subdivision!'
						indexnumbermatch = i
						print 'indexnumbermatch',indexnumbermatch
						print 'matching', correctSubdivision
						correctSubdivision = doc.getElementsByTagName("xls:Building")[i].getAttribute('subdivision')
						break
					else:
						indexnumbermatch = 0
			except:
				correctSubdivision = ''
				indexnumbermatch = 0
				
			try:
				correctAddress = doc.getElementsByTagName("xls:Street")[indexnumbermatch].firstChild.nodeValue
			except:
				correctAddress = ''
			try:
				correctPostalcode = doc.getElementsByTagName("xls:PostalCode")[indexnumbermatch].firstChild.nodeValue
			except:
				correctPostalcode = ''
			try:
				correctBuildingnumber = doc.getElementsByTagName("xls:Building")[indexnumbermatch].getAttribute('number')
			except:
				correctBuildingnumber = ''
			
			print '%r' % addressname
			inserted_address = re.sub(r'[.aeyuijo\s\W]','',addressname.lower().strip())
			print 'inserted address:', inserted_address 
			pdok_address = re.sub(r'[.aeyuijo\s\W]','',correctAddress.lower().strip())
			print 'pdok address    :', pdok_address

			# check if addressnames match
			if inserted_address == pdok_address:
				print 'It\'s a match!'
				# return doc, correctAddress, correctBuildingnumber, correctSubdivision, correctPostalcode, url, indexnumbermatch
					
				X,Y,Latitude,Longitude = getXYandLatLon()
				matchfound = 'yes'
				print "Found matching BAG address FIRST RUN!"
			else:
				# check if letters within addressnames match
				if all(c in inserted_address for c in pdok_address):
					X,Y,Latitude,Longitude = getXYandLatLon()
					matchfound = 'yes'
					print "Found matching BAG address FUZZY RUN!"
				else:
					print 'no geo coordinates information found in XML'
					matchfound = 'no'
			
			print matchfound
			if matchfound == 'yes':
				row.extend([correctAddress.encode("utf-8"), correctBuildingnumber, correctSubdivision, correctPostalcode,X,Y,Latitude,Longitude])
				print row
				writer.writerow(row)
				print "Found matching BAG address!"
				return matchfound
		
	except Exception, e:
		print 'bad exit', e
		matchfound = 'no'
		return matchfound
	

# --------------------------------------------------------------
#  Read the CSV file header
# --------------------------------------------------------------

infile = codecs.open(from_file, 'r')
dialect = csv.Sniffer().sniff(infile.readline(), [',',';',';','|'],)
infile.seek(0)
reader = csv.reader(infile, dialect)
# read first line and add cells into header variable
header = reader.next()

# print id's for each header
for i in range(0,len(header)):
	print '%d. %s \n' % (i, header[i])

header.extend(['BAG Straatnaam','BAG Huisnummer','BAG Toevoeging','BAG Postcode','X','Y','Latitude','Longitude'])


# --------------------------------------------------------------
#  Set input fields and format as integers
# --------------------------------------------------------------
addressindex = raw_input('choose address column number: ')
addresscol = int(addressindex)

numberindex = raw_input('choose house number column id (hit return if none present): ')
if numberindex:
	numbercol = int(numberindex)

levelindex = raw_input('choose level column number (hit return if none present): ')
if levelindex:
	levelcol = int(levelindex)

postalcodeindex = raw_input('choose postal code column number (hit return if none present): ')
if postalindex:
	postalcodeindex = int(postalcodeindex)

# from_file = raw_input("Please type in your filename.csv (example_files/address.csv): ")
city_yn = raw_input("Does your file has a city column? (choose Y/N): ")

if city_yn.upper() == 'Y':
	cityindex = raw_input('choose city column number: ')
	if cityindex:
		citycol = int(cityindex)

if city_yn.upper() == 'N':
	city_manually = raw_input("Please fill in the city name to match the locations in the file (Amsterdam): ")


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

	
# --------------------------------------------------------
# loop through each row in csv file
# --------------------------------------------------------
for row in reader:	
	# failsave to ignore whitespace at the end of the csv
	if row:
		# set line variables
		addressname = ""
		number = ""
		level = ""
		letter = ""
		postalcode = ""	
		# check which columns are found and generate a generic address line
		
		if lettercol is '' and numbercol and levelcol:
			print 'lettercol is none and numbercol and levelcol'
			
			# for each column do set 'line' as input for api geocoder with corresponding column id's
			line ='%s %s %s' % (row[addresscol],row[numbercol],row[levelcol])
			print 'found line with housenumber and level: %s' % line
		
		elif levelcol is '' and numbercol:
			
			print 'levelcol is none and numbercol'
			
			# for each column do...
			line ='%s %s' % (row[addresscol],row[numbercol])
			print 'found line with housenumber: %s' % line
		
		else:
			print 'just one addressline'
			
			# for each column do...
			line ='%s' % row[int(addresscol)]
			print 'found line total address line: %s' % line

		recordcount += 1	


		# --------------------------------------------------------
		# Do A Basic Cleanup For Each Cell Type
		# --------------------------------------------------------

		cleanupwords = [[
						# remove ,
						[r',',''],
						# remove everything between () including the brackets
						[r'\(.*\)', ''],
						# remove near ... or across a ... words
						[r'\btegenover\b|\bnabij\b|\bt/o\b|\bvlakbij\b|\bsupermarkt\b|\bah\b',''],
						# remove everything between () including the brackets
						[r'(unit|kamer|afdeling)(\s+.*\b)', ''],
						# replace v. for van
						[r'v\.', 'van'],
						# remove space between postal code
						[r'(\d{4})(\s+)([A-Z]{2})', r'\1\3'],
						# rename all writing styles of Ground FLoor subdivision to H
						[r'(\s+|-)(HS|huis|BG|bel|"begane grond")','H'],
						# rename al writing styles of BIS to BS
						[r'(?=\s+|-)BIS\s','BS'],
						# split 1234hg to 123 4
						[r'(?=\d+)([0-9])(hg|hoog)',r' \1'],
						# remove hg, hoog, etage
						[r'(?!\d+)([\s-]*)hg|hoog|etage\b',''],
						# replace roman subdivision with numbers
						[r'(\s*|-)III\b',' 3'],
						[r'(\s*|-)II',' 2'],
						[r'(\s|-)I\b',' 1 '],
						# replace rood/zwart by RDA/ZWA
						[r'([\s-]+)Rood\b','RDA'],
						[r'([\s-]+)Zwart\b','ZWA'],
						# rename str to straat where it stands on the end a word and continues by a whitespace
						[r'(?=\w+)str(?=\s|\.)','straat'],
						# rename ln to laan where it stands on the end a word and continues by a whitespace
						[r'(?=\w+)ln(?=\s|\.)','laan'],
						# rename pr to prins
						[r'\b(pr|pr\.)\b','prins '],
						# rename adm to admiraal
						[r'Adm(\s+|\.)','Admiraal '],
						# add - by churchill-laan
						[r'lllaan','ll-laan'],
						# remove everything between () including the brackets
						[r'\s{1,5}', ' '],
						# remove weird characters
						[r'\.+',' ']
						],
						[
						[r'(\s+)(ZUIDOOST|zuid-oost|DR|Drenthe|FL|Flevoland|FR|Friesland|GD|Gelderland|GR|Groningen|LB|Limburg|NB|Noord-Brabant|NH|Noord-Holland|OV|Overijssel|UT|Utrecht|ZH|Zuid-Holland|ZL|Zeeland)','']
						]
						]

		for i in range(len(cleanupwords[0])):
			if re.sub(cleanupwords[0][i][0],cleanupwords[0][i][1],line):
				print 'Cleaned %s --> %s' % (cleanupwords[0][i][0],cleanupwords[0][i][1])
			line = re.sub(cleanupwords[0][i][0],cleanupwords[0][i][1], line, flags=re.I)
		print 'cleaned up line: %s' % line

		# Get city names from column, else from manually inserted name	
		if city_yn.upper() == 'Y':
			city = '%s' % row[citycol].strip() 
		else:
			city = '%s' % city_manually

		# remove province additions to get a proper result back
		city = re.sub(cleanupwords[1][0][0],cleanupwords[1][0][1], city, re.M|re.I)
		print 'city cleaned Province name: %s' % city

	
		# --------------------------------------------------------
		# Find and Set 4 variables based on a total address line
		# --------------------------------------------------------	
				
		matchvar = [['addressname',r'(^.*?(?=(\s+\d+)))'],
					['postalcode',r'(\d{4}\w{2})'],
					['number',r'(?!\d{4}\w{2})(\s+)(\d+)'],
					['level',r'([a-zA-Z]+\s+\d+)([\s|-]{1})(\d+)'],
					['letter',r'([a-zA-Z]+\s+\d+)(\s*|-)([a-zA-Z]{1,3}\b)']]
		
		# set emtpy loop named variable (v0, v1, etc...)
		d={}

		for i in range(len(matchvar)):	
			typename = matchvar[i][0]
			# print typename
			matchcrit =  matchvar[i][1]
			# print matchcrit
	
			matchonvarfound = re.search(matchcrit, line, re.M|re.I)
	
			if matchonvarfound:
				try:
					# to get letter en level properly
					if matchonvarfound.group(3):
						d["v{0}".format(i)] = matchonvarfound.group(3).strip()
				except:
					# to get addressname properly
					d["v{0}".format(i)] = matchonvarfound.group().strip()
				globals()[typename] = d["v{0}".format(i)]
				print "%s: %s" % (typename, d["v{0}".format(i)])
				
			else:
				print 'No %s match found.' % typename
				nonefound+=1
				d["v{0}".format(i)] = '' 
				print typename
		print addressname

		if not addressname and not postalcode:
			addressname = '%s' % line
		
	 	if postalcodecol !='':
	 		#postalcodecol = int(postalcodeindex)
	 		postalcode = row[postalcodecol]
		
		print nonefound
		
		# if there are no varible matches found, just use entire line, it is probably an address without number
		if nonefound==5:
			print 'ja'
			addressname = line

		# --------------------------------------------------------
		# build up the address with convention for api pdok.nl
		# -------------------------------------------------------- 	
		# TODO postcode en huisnummer voor 'é en è die niet oplosbaar is: M.J. Granpré Molièreplein 1064DG Amsterdam'

		if postalcodeindex and number:
			print 'try postalcode and housenumber'
			total_address = '%s+%s+%s' %(row[int(postalcodeindex)],int(number),city)
			print total_address
			getXMLpdok(total_address)
			if matchfound == 'yes':
				print 'Geocoded with postal code and house number'
			else:
				print 'try postalcode and housenumber -2'
				total_address = '%s+%s+%s' %(row[int(postalcodeindex)],int(number)-2,city)
				getXMLpdok(total_address)
				if matchfound == 'yes':
					print "Match with postalcode and housnumber -2!"
		if number =='':
			print 'try only address'
			total_address = '%s+%s' % (addressname,city)
			print total_address
			getXMLpdok(total_address)
			if matchfound == 'yes':
				print 'Geocoded with address'
			else: 
				print 'notfound 4'
				notfoundcount += 1
				notwriter.writerow(row)
		else: 
			if addressname and number is not "":	
				print 'try addressname and housenumber'
				total_address = '%s+%s+%s' % (addressname,number,city)
				getXMLpdok(total_address)
				if matchfound == 'no':	
					print 'Address not found, trying word replacements...'
					# this is a dictionary where the words are replaced,
					replacewords = [
					[r'1e|1ste', 'Eerste'],['2ste','Tweede'],['3ste','Tweede'],['BS',''],['BSA','A'],['BSB','B'],['BSC','C'],['BSD','D'],
					#['straat','weg'],['ij','y'],['y','ij'],['weg','straat'],['ij','y'],['y','ij'],	
					['burgemeester','burgermeester'],['burgermeester','burgemeester'],
					['sen','ssen'],['ssen','sen'],
					#['laan','plein'],['plein','laan'],
					[r'(?!e)straat','sstraat'],['ij','y'],['y','ij'],['sstraat','straat'],
					['prins','prinses']]						

					print "if address name is mismatch run first cleanup, correct address writing from '1e' to 'Eerste' for example"
					# loop through each word
					i = None
					for i in range(len(replacewords)):
						m = re.search(replacewords[i][0],addressname, flags=re.I)
						print 'replacing %s for %s' % (replacewords[i][0], replacewords[i][1])
						print m
						if m is not None: 
							addressname = re.sub(replacewords[i][0],replacewords[i][1],addressname, flags=re.I)
							print addressname
							total_address = addressname+'+'+number+'+'+city
							getXMLpdok(total_address)
							if matchfound == 'yes':
								print "Match with word %s replaced!" % replacewords[i][1]
								break							
					else:
						if int(number) >2:
							if level !='':
								total_address = addressname+'+'+level+'+'+city	
								getXMLpdok(total_address)
								if matchfound == 'yes':
									print "Match with only last house number!"
							else:
								number_2lower = int(number)-2
								total_address = '%s+%s+%s' %(addressname,number_2lower,city)
								getXMLpdok(total_address)
								if matchfound == 'yes':
									print "Match with housnumber -2!"
								else:					
									number_2higher = int(number)+2
									total_address = '%s+%s+%s' %(addressname,number_2higher,city)
									getXMLpdok(total_address)
									if matchfound == 'yes':
										print "Match with housnumber +2!"
							
						else:
							# if there is no match, write the row to the notfound csv		
							print 'Replacing words failed ', e
							print 'notfound 1'
							notfoundcount += 1
							notwriter.writerow(row)

			else:
				print 'try postal code'
				# if there is no number value found, assume it is a postal code, so do this:
				total_address = postalcode+'+'+city
				print total_address
				getXMLpdok(total_address)
				if matchfound == 'yes':
					print 'Geocoded with postal code'
				else: 
					print 'notfound 3'
					notfoundcount += 1
					notwriter.writerow(row)