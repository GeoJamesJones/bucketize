# bucketize

required packages

pip install beautifulsoup4 google

# sample query

python bucketize.py -q "Japan Food Production" -m 10 -d /Users/jame9353/Documents/temp_data/harvest -c "Food Production Center" -g http://wdcrealtimeevents.esri.com:6180/geoevent/rest/receiver/ca-query-in

python bucketize.py -q "Japan Food Distribution" -m 10 -d /Users/jame9353/Documents/temp_data/harvest -c "Food Distribution" -g http://wdcrealtimeevents.esri.com:6180/geoevent/rest/receiver/ca-query-in

python bucketize.py -q "Japan Warehouse" -m 10 -d /Users/jame9353/Documents/temp_data/harvest -c "Warehouse/Storage Facility" -g http://wdcrealtimeevents.esri.com:6180/geoevent/rest/receiver/ca-query-in