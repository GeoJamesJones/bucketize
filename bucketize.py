import argparse
import requests
import os
import urllib3
from bs4 import BeautifulSoup

try: 
    from googlesearch import search 
except ImportError:  
    print("No module named 'google' found")

def netowl_curl(infile, outpath, outextension, netowl_key):
    """Do James Jones code to query NetOwl API."""
    headers = {
        'accept': 'application/json',  # 'application/rdf+xml',
        'Authorization': netowl_key,
    }

    if infile.endswith(".txt"):
        headers['Content-Type'] = 'text/plain'
    elif infile.endswith(".pdf"):
        headers['Content-Type'] = 'application/pdf'
    elif infile.endswith(".docx"):
        headers['Content-Type'] = 'application/msword'

    params = {"language": "english", "text": "", "mentions": ""}

    data = open(infile, 'rb').read()
    response = requests.post('https://api.netowl.com/api/v2/_process',
                             headers=headers, params=params, data=data,
                             verify=False)

    r = response.text
    outpath = outpath
    filename = os.path.split(infile)[1]
    if os.path.exists(outpath) is False:
        os.mkdir(outpath, mode=0o777, )
    outfile = os.path.join(outpath, filename + outextension)
    open(outfile, "w", encoding="utf-8").write(r)
  
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-q", "--query", help="Query for Google Search", required=True)
    parser.add_argument("-m", "--max", help="Max number of results to return", required=True)
    parser.add_argument("-d", "--directory", help="Directory to write text files harvested from the web.", required=True)
    args = parser.parse_args()
    # to search 
    query = args.query

    urllib3.disable_warnings()

    netowl_key = 'netowl ff5e6185-5d63-459b-9765-4ebb905affc8'

    count = 0
  
    for j in search(query, tld="co.in", num=int(args.max), stop=10, pause=2):
        count +=1
        r = requests.get(j)
        soup = BeautifulSoup(r.content)

        soup_list = [s.extract() for s in soup(['style', 'script', '[document]', 'head', 'title'])]
        visible_text = soup.getText()

        print(visible_text)

        filename = args.query.replace(" ", "_") + str(count)
        text_file_path = os.path.join(args.directory, filename + '.txt')
        with open(text_file_path, 'w') as text_file:
            text_file.write(visible_text)
            text_file.close()

        netowl_curl(text_file_path, args.directory, ".json", netowl_key)

if __name__=="__main__":    
    main()