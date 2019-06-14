#Copyright (c) Microsoft Corporation. All rights reserved.
#Licensed under the MIT License.

# -*- coding: utf-8 -*-

import http.client 
import urllib.parse
import requests
import os
import json
import string
import urllib3

import PySimpleGUI as sg 

from bs4 import BeautifulSoup
from random import randint

urllib3.disable_warnings()

# **********************************************
# *** Update or verify the following values. ***
# **********************************************

# Replace the subscriptionKey string value with your valid subscription key.
subscriptionKey = "8320c5adb10f4616a69120664200cb9e"

# Verify the endpoint URI.  At this writing, only one endpoint is used for Bing
# search APIs.  In the future, regional endpoints may be available.  If you
# encounter unexpected authorization errors, double-check this value against
# the endpoint for your Bing Web search instance in your Azure dashboard.
host = "api.cognitive.microsoft.com"
path = "/bing/v7.0/search"

# NetOwl Class Objects
class NetOwl_Entity:
    """Class to hold entities extracted from NetOwl API"""
    
    def __init__(self, value_dict=None): 
        """Docstring."""

        if 'id' in value_dict:
            self.id = value_dict['id']
        if 'ontology' in value_dict:
            self.ontology = value_dict['ontology']
        if 'value' in value_dict:
            self.value = value_dict['value']
        if 'norm' in value_dict:
            self.norm = value_dict['norm']
        if 'head' in value_dict:
            self.pre_text = value_dict['head']
        if 'tail' in value_dict:
            self.post_text = value_dict['tail']
        if 'doc_link' in value_dict:
            self.doc_link = value_dict['doc_link']
        if 'query' in value_dict:
            self.query = value_dict['query']
        if 'category' in value_dict:
            self.category = value_dict['category']

        if 'geo_entity' in value_dict:
            self.geo_entity = value_dict['geo_entity']
            self.loc = [value_dict['long'], value_dict['lat']]
            self.lat = value_dict['lat']
            self.long = value_dict['long']
            self.geo_type = value_dict['geo_type']
            self.geo_subtype = value_dict['geo_subtype']
        else:
            self.geo_entity = False

def BingWebSearch(search):
    "Performs a Bing Web search and returns the results."

    headers = {'Ocp-Apim-Subscription-Key': subscriptionKey}
    conn = http.client.HTTPSConnection(host)
    query = urllib.parse.quote(search)
    conn.request("GET", path + "?q=" + query, headers=headers)
    response = conn.getresponse()
    headers = [k + ": " + v for (k, v) in response.getheaders()
                   if k.startswith("BingAPIs-") or k.startswith("X-MSEdge-")]
    return headers, response.read().decode("utf8")

def cleanup_text(intext):
    """Function to remove funky chars."""
    printable = set(string.printable)
    p = ''.join(filter(lambda x: x in printable, intext))
    g = p.replace('"', "")
    return g

def geocode_address(address):
    """Use World Geocoder to get XY for one address at a time."""
    querystring = {
        "f": "json",
        "singleLine": address}
    url = "https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates"  # noqa: E501
    response = requests.request("GET", url, params=querystring)
    p = response.text
    j = json.loads(p)
    location = j['candidates'][0]['location']  # returns first location as X, Y
    return location

def get_head(text, headpos, numchars):
    """Return text before start of entity."""
    wheretostart = headpos - numchars
    if wheretostart < 0:
        wheretostart = 0
    thehead = text[wheretostart: headpos]
    return thehead

def get_tail(text, tailpos, numchars):
    """Return text at end of entity."""
    wheretoend = tailpos + numchars
    if wheretoend > len(text):
        wheretoend = len(text)
    thetail = text[tailpos: wheretoend]
    return thetail

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

def post_to_geoevent(json_data, geoevent_url):
    headers = {
        'Content-Type': 'application/json',
                }

    response = requests.post((geoevent_url), headers=headers, data=json_data)

def process_netowl_json(document_file, json_data, web_url, query_string, category, date_crawled, snippet, language):
    doc_entities = []
    doc_links = []
    doc_events = []
    
    # Open main portion of output NetOwl JSON
    if 'document' in json_data:
        document = json_data['document'][0]

        if 'text' in document:
            content = document['text'][0]['content']
                        
        if 'entity' in document:
            # Build entity objects
            ents = (document['entity'])  # gets all entities in doc

            # Iterates through entities in the document
            for e in ents:
                base_entity = {}

                # gather data from each entity
                rdfvalue = cleanup_text(e['value'])  # value (ie name)
                rdfid = e['id']
                rdfid = document_file.split(".")[0] + "_e_" + rdfid  # unique to each entity
                e['id'] = rdfid

                base_entity['id'] = rdfid

                if 'ontology' in e:
                    base_entity['ontology'] = e['ontology']
                if 'value' in e:
                    base_entity['value'] = e['value']
                if 'norm' in e:
                    base_entity['norm'] = e['norm']

                if 'geodetic' in e:
                    base_entity['geo_entity'] = True
                    base_entity['lat'] = float(e['geodetic']['latitude'])
                    base_entity['long'] = float(e['geodetic']['longitude'])

                # check for addresses
                if e['ontology'] == "entity:address:mail":
                    address = e['value']
                    location = geocode_address(address)  # returns x,y

                    base_entity['geo_entity'] = True
                    base_entity['lat'] = location['y']
                    base_entity['long'] = location['x']
                    
                # Sets the type of the geo-entity to allow for better symbology

                if 'geo_entity' in base_entity:
                    base_entity['geo_type'] = "placename"
                    base_entity['geo_subtype'] = "unknown"

                    if e['ontology'] == "entity:place:city":
                        base_entity['geo_type'] = "placename"
                        base_entity['geo_subtype'] = "city"
                    if e['ontology'] == "entity:place:country":
                        base_entity['geo_type'] = "placename"
                        base_entity['geo_subtype'] = "country"
                    if e['ontology'] == "entity:place:province":
                        base_entity['geo_type'] = "placename"
                        base_entity['geo_subtype'] = "province"
                    if e['ontology'] == "entity:place:continent":
                        base_entity['geo_type'] = "placename"
                        base_entity['geo_subtype'] = "continent"
                    if e['ontology'] == "entity:numeric:coordinate:mgrs":
                        base_entity['geo_type'] = "coordinate"
                        base_entity['geo_subtype'] = "MGRS"
                    if e['ontology'] == "entity:numeric:coordinate:latlong":
                        base_entity['geo_type'] = "coordinate"
                        base_entity['geo_subtype'] = "latlong"
                    if e['ontology'] == "entity:address:mail":
                        base_entity['geo_type'] = "address"
                        base_entity['geo_subtype'] = "mail"
                    if e['ontology'] == "entity:place:other":
                        base_entity['geo_type'] = "placename"
                        base_entity['geo_subtype'] = "descriptor"
                    if e['ontology'] == "entity:place:landform":
                        base_entity['geo_type'] = "placename"
                        base_entity['geo_subtype'] = "landform"
                    if e['ontology'] == "entity:organization:facility":
                        base_entity['geo_type'] = "placename"
                        base_entity['geo_subtype'] = "facility"
                    if e['ontology'] == "entity:place:water":
                        base_entity['geo_type'] = "placename"
                        base_entity['geo_subtype'] = "water"
                    if e['ontology'] == "entity:place:county":
                        base_entity['geo_type'] = "placename"
                        base_entity['geo_subtype'] = "county"
                
                if 'entity-mention' in e:
                    em = e['entity-mention'][0]
                    if 'head' in em:
                        base_entity['head'] = get_head(content, int(em['head']), 255)
                    if 'tail' in em:
                        base_entity['tail'] = get_tail(content, int(em['tail']), 255)

                base_entity['url'] = web_url
                base_entity['query'] = query_string
                base_entity['category'] = category
                base_entity['snippet'] = snippet
                base_entity['date_indexed'] = date_crawled
                base_entity['language'] = language

                # Turns entity information into a class object for storage and transformation
                netowl_entity_object = NetOwl_Entity(base_entity)
                doc_entities.append(netowl_entity_object)
                
        return doc_entities

def main():

    layout = [  
          [sg.Text('Query'), sg.Input(do_not_clear=True, key='_QUERY_')],
          [sg.Text('Category'), sg.Listbox(values=('Warehouse/Storage Facility', 
                                                   'Commercial Food Distribution Center', 
                                                   'Farm/Ranch',
                                                   'Food Distribution',
                                                   'Food Production Center',
                                                   'Food Retail',
                                                   'Grain Storage',
                                                   'Generation Station', 
                                                   'Natural Gas Facility',
                                                   'Petroleum Facility',
                                                   'Propane Facility',
                                                   'Government Site Infrastructure',
                                                   'Medical Treatment Facility (Hospital)',
                                                   'Civilian Television'), key='_CATEGORY_',
                                                   size=(30, 3))],
          [sg.Text('GeoEvent URL'), sg.Input(do_not_clear=True, key='_GeoEvent_')],
          [sg.Text('NetOwl API Key'), sg.Listbox(values=('netowl ff5e6185-5d63-459b-9765-4ebb905affc8',
                                                            'none'), key='_NETOWL_',
                                                   size=(30, 3))],
          [sg.Text('Message:'), sg.Text('                                                                                                ', key='_OUTPUT_') ],
          [sg.Button('Submit'), sg.Button('Exit')]]  

    window = sg.Window('Window Title').Layout(layout)

    while True:                 # Event Loop  
        event, values = window.Read()  
        print(event, values)
        if event is None or event == 'Exit':  
            break  
        if event == 'Submit':  
            # change the "output" element to be the value of "input" element  
            window.FindElement('_OUTPUT_').Update(values['_QUERY_'])

            term = values['_QUERY_']
            category = values['_CATEGORY_'][0]
            directory = r'/Users/jame9353/Documents/temp_data/bucketize/bing'
            netowl_key = values['_NETOWL_'][0]
            geoevent_url = values['_GeoEvent_']

            if len(subscriptionKey) == 32:

                print('Searching the Web for: ', term)

                headers, result = BingWebSearch(term)
                print("\nRelevant HTTP Headers:\n")
                print("\n".join(headers))
                print("\nJSON Response:\n")
                try:
                    for value in json.loads(result)['webPages']['value']:
                        print(json.dumps(value, indent=4))

                        r = requests.get(value['url'], verify=False, timeout=10)
                        soup = BeautifulSoup(r.content, features="html.parser")

                        soup_list = [s.extract() for s in soup(['style', 'script', '[document]', 'head', 'title'])]
                        visible_text = soup.getText()

                        filename = term.replace(" ", "_") + str(randint(1,1000))
                        text_file_path = os.path.join(directory, filename + '.txt')
                        with open(text_file_path, 'w', encoding='utf-8') as text_file:
                            print_text = cleanup_text(visible_text)
                            text_file.write(print_text)
                            text_file.close()

                        netowl_curl(text_file_path, directory, ".json", netowl_key)

                        with open(text_file_path + ".json", 'rb') as json_file:
                            data = json.load(json_file)

                            entity_list = process_netowl_json(filename, data, value['url'], term, category, value['dateLastCrawled'], value['snippet'], value['language'])

                            spatial_entities = []
                            
                            for entity in entity_list:
                                if entity.geo_entity == True:
                                    if entity.geo_type == 'coordinate' or entity.geo_type == 'address' or entity.geo_subtype == 'city':
                                        spatial_entities.append(vars(entity))
                        
                        os.remove(text_file_path)
                        os.remove(text_file_path + ".json")

                        #post_to_geoevent(spatial_entities, geoevent_url)
                        print(spatial_entities)
                
                except Exception as e:
                    print(str(e))

            else:

                print("Invalid Bing Search API subscription key!")
                print("Please paste yours into the source code.")

if __name__ == "__main__":
    main()