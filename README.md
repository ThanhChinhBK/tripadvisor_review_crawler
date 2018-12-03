# Trip Advisor crawler

This is a simple crawler script for Trip Advisor.

It is aimed at researchers and students that want to experiment with text mining problems on review data.

### usage: 
>>      python3 trip-advisor-crawler.py [-h] [-f] [-a {Hotel,Restaurant}]
>>                                      [-r MAXRETRIES] [-t TIMEOUT] [-p PAUSE]
>>                                      [-m MAXREVIEWS] -o OUT
>>                                      ID [ID ...]

### ID format:
* domain:locationcode, e.g. com:187768 reviews of hotels in Italy from the com domain
* domain:locationcode:citycode, e.g. jp:187899:187899 city of Pisa from the jp domain 
* domain:locationcode:citycode:hotelcode, e.g. it:187899:187899:662603 all reviews for a specific hotel from the it domain
* domain:locationcode:citycode:hotelcode:reviewcode, e.g. it:187899:187899:662603:322965103 a specific review

### positional arguments:
  ID                    IDs for which to download reviews

### optional arguments:
  
  -h, --help            show this help message and exit
  
  -f, --force           Force download even if already successfully downloaded
  
  -a {Hotel,Restaurant}, --activity {Hotel,Restaurant}
                        Type of activity to crawl (default: Hotel)
  
  -r MAXRETRIES, --maxretries MAXRETRIES
                        Max retries to download a file. Default: 3
  
  -t TIMEOUT, --timeout TIMEOUT
                        Timeout in seconds for http connections. Default: 360
  
  -p PAUSE, --pause PAUSE
                        Seconds to wait between http requests. Default: 0.5
  
  -m MAXREVIEWS, --maxreviews MAXREVIEWS
                        Maximum number of reviews per item to download.
                        Default:unlimited
  
  -o OUT, --out OUT     Output base path
