PDOK_address_geocoder_csv2csv
=============================

Dutch address bulk geocoder from CSV to CSV by using the PDOK api for address coordinates retrieval in RD and WGS84.<br>

This python script loops through different corrections and cleanup actions when nothing is found untill the address name matches.<br>
The api uses <i>http://geodata.nationaalgeoregister.nl/geocoder/Geocoder?zoekterm="</i> + address + number + subdivision + city<br>

usage: 
Use the terminal or command line <br>>>> python address_cleanup_pdok.py <i>your_filename.csv</i><br><br>
output:<br>
This wil output the file as:<br>
<i>your_filename</i>_BAG_geocoded.csv<br>
and<br>
<i>your_filename</i>_BAG_notfound.csv<br>
for debugging and list of mismatched addresses
