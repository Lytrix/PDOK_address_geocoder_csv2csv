PDOK_address_geocoder_csv2csv
=============================

Dutch address bulk geocoder from CSV to CSV by using the PDOK api for address coordinates retrieval in RD and WGS84.<br>

This python script loops through different corrections and cleanup actions when nothing is found untill the address name matches.<br>
The script tries to look for regular used column names and uses these to add to the api. The api is filled with each cel that is found in these columns which contains:
address (with number and subdivision in one cell), address and number separate or addres, number, subdivision separate.<br>
Keep in mind, there must be at least an address and city column, else the geocoder will not work properly:<br> <i>http://geodata.nationaalgeoregister.nl/geocoder/Geocoder?zoekterm="</i>+address+number+subdivision+ city<br><br>
<b>usage:</b> <br>
Use the terminal or command line <br>>>> python address_cleanup_pdok.py <i>your_filename.csv</i><br><br>
output:<br>
This wil output the file as:<br>
<i>your_filename</i>_BAG_geocoded.csv<br>
and<br>
<i>your_filename</i>_BAG_notfound.csv<br>
for debugging and list of mismatched addresses
