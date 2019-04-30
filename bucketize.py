import argparse
import requests
import os
import json
import string
import urllib3
import time
from bs4 import BeautifulSoup

from GPLogger import GPLogger

try: 
    from googlesearch import search_news 
except ImportError:  
    print("No module named 'google' found")

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

    def toJSON(self):
        """Method to turn class into JSON object"""
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True, indent=4)

class NetOwl_Link:
    """Class to hold links extracted from NetOwl API"""
    
    def __init__(self, value_dict=None): 
        """Docstring."""
        
        if 'value' in value_dict:
            self.value = value_dict['value']
        if 'norm' in value_dict:
            self.norm = value_dict['norm']
        if 'ontology' in value_dict:
            self.ontology = value_dict['ontology']
        if 'role' in value_dict:
            self.role = value_dict['role']
        if 'role-type' in value_dict:
            self.role_type = value_dict['role-type']
        if 'role' in value_dict:
            self.link_role = value_dict['link-role']
        if 'role-type' in value_dict:
            self.link_role_type = value_dict['link-role-type']
        if 'value' in value_dict:
            self.link_value = value_dict['link-value']
        if 'value-type' in value_dict:
            self.link_value_type = value_dict['link-value-type']
        if 'idref' in value_dict:
            self.link_id = value_dict['link-id']
        if 'ent-ontology' in value_dict:
            self.ent_ontology = value_dict['ent-ontology']
        if 'link-ontology' in value_dict:
            self.link_ontology = value_dict['link-ontology']
            
    def toJSON(self):
        """Method to turn class into JSON object"""
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True, indent=4)
    
class NetOwl_Event:
    """Class object to hold events extracted by the NetOwl API"""
    
    def __init__(self, value_dict=None): 
        """Docstring."""
        
        self.event_role = value_dict['event-role']
        self.event_value = value_dict['event-value']
        self.event_value_type = value_dict['event-value-type']
        self.event_id = value_dict['event-id']
        self.predicate = value_dict['predicate']
        self.ent_ontology = value_dict['ent-ontology']
            
        if 'triple' in value_dict:
            self.arg_role = value_dict['arg-role']
            self.arg_value = value_dict['arg-value']
            self.arg_value_type = value_dict['arg-value-type']
            self.arg_id = value_dict['arg-id']
            self.arg_ontology = value_dict['arg-ontology']
            self.triple = value_dict['triple']
        else:
            self.triple = False
            
    def toJSON(self):
        """Method to turn class into JSON object"""
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True, indent=4)

class Text_Item:
    """Class to hold text content derived from NetOwl API"""
    
    
    def __init__(self, doc_id=None, text_content=None): 
        """Docstring."""
        self.id = doc_id
        self.content = text_content
        
        
    def toJSON(self):
        """Method to turn class into JSON object"""
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True, indent=4)

def process_netowl_json(document_file, json_data, web_url, query_string, category):
    doc_entities = []
    doc_links = []
    doc_events = []
    
    # Open main portion of output NetOwl JSON
    if 'document' in json_data:
        document = json_data['document'][0]
                    
        # Extract source text that is embedded in NetOwl JSON and save it as a Text_Item class object
        if 'text' in document:
            content = document['text'][0]['content']
                        
            content_object = Text_Item(doc_id=document_file, text_content=content)
                        
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

                base_entity['doc_link'] = web_url
                base_entity['query'] = query_string
                base_entity['category'] = category

                # Turns entity information into a class object for storage and transformation
                netowl_entity_object = NetOwl_Entity(base_entity)
                doc_entities.append(netowl_entity_object)

                # Returns extracted links from the entity
                if 'link-ref' in e:
                    base_entity['has_links'] = True

                    base_link = {}

                    base_link['id'] = rdfid

                    if 'value' in e:
                        base_link['value'] = e['value']
                    if 'norm' in e:
                        base_link['norm'] = e['norm']
                    link_ref = e['link-ref']
                    for link in link_ref:
                        if 'ontology' in link:
                            base_link['ontology'] = link['ontology']
                        if 'role' in link:
                            base_link['role'] = link['role']
                        if 'role-type' in link:
                            base_link['role-type'] = link['role-type']
                        if 'role' in link['entity-arg'][0]:
                            base_link['link-role'] = link['entity-arg'][0]['role']
                        if 'role-type' in link['entity-arg'][0]:
                            base_link['link-role-type'] = link['entity-arg'][0]['role-type']
                        if 'value' in link['entity-arg'][0]:
                            base_link['link-value'] = link['entity-arg'][0]['value']
                        if 'value-type' in link['entity-arg'][0]:
                            base_link['link-value-type'] = link['entity-arg'][0]['value-type']
                        if 'idref' in link['entity-arg'][0]:
                            base_link['link-id'] = document_file.split(".")[0] + "_e_" + link['entity-arg'][0]['idref']
                        if 'ontology' in link:
                            base_link['link-ontology'] = link['entity-arg'][0]['ontology']
                            base_link['ent-ontology'] = e['ontology']

                        netowl_link_object = NetOwl_Link(base_link)
                        doc_links.append(netowl_link_object)
            
        # Determines if there are extracted links in the document
        if 'link' in document:
            links = (document['link'])
            for link in links:
                base_link = {}
                
                base_link['ontology'] = link['ontology']
                entity_arg1 = link['entity-arg'][0]
                entity_arg2 = link['entity-arg'][1]
                
                base_link['role'] = entity_arg1['role']
                base_link['role-type'] = entity_arg1['role-type']
                base_link['value'] = entity_arg1['value']
                base_link['role'] = entity_arg1['role']
                base_link['id'] = document_file.split(".")[0] + "_e_" + entity_arg1['idref']
                base_link['ent-ontology'] = entity_arg1['ontology']
                base_link['link-role'] = entity_arg2['role']
                base_link['link-role-type'] = entity_arg2['role']
                base_link['link-value'] = entity_arg2['value']
                base_link['link-value-type'] = entity_arg2['value-type']
                base_link['link-id'] = document_file.split(".")[0] + "_e_" + entity_arg2['idref']
                base_link['link-ontology'] = entity_arg2['ontology']
                
                netowl_link_object = NetOwl_Link(base_link)
                doc_links.append(netowl_link_object)

        # Determines if there are extracted events in the document
        if 'event' in document:
            events = (document['event'])
            for event in events:
                base_event = {}
                
                event_args = event['entity-arg']
                event_properties = event['property'][0]
                    
                
                base_event['event-role'] = event_args[0]['role']
                base_event['event-value'] = event_args[0]['value']
                base_event['event-value-type'] = event_args[0]['value-type']
                base_event['event-id'] = document_file.split(".")[0] + "_e_" + event_args[0]['idref']
                base_event['ent-ontology'] = event_args[0]['ontology']
                base_event['predicate'] = event_properties['value']
                
                if len(event['entity-arg']) > 1:
                    count = 0
                    for arg in event_args:
                        count +=1
                        if count == 1:
                            pass
                        else:
                            arg_dict = base_event.copy()
                            event_arg = event['entity-arg'][1]
                            arg_dict['arg-role'] = arg['role']
                            arg_dict['arg-value'] = arg['value']
                            arg_dict['arg-value-type'] = arg['value-type']
                            arg_dict['arg-id'] = document_file.split(".")[0] + "_e_" + arg['idref']
                            arg_dict['arg-ontology'] = arg['ontology']
                            arg_dict['triple'] = True
                    
                            netowl_event_object = NetOwl_Event(arg_dict)
                            doc_events.append(netowl_event_object)

                else:
                    netowl_event_object = NetOwl_Event(base_event)
                    doc_events.append(netowl_event_object)
                
        return doc_entities, doc_links, doc_events

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

def post_to_geoevent(json_data, geoevent_url):
    headers = {
        'Content-Type': 'application/json',
                }

    response = requests.post((geoevent_url), headers=headers, data=json_data)
  
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-q", "--query", help="Query for Google Search", required=True)
    parser.add_argument("-m", "--max", help="Max number of results to return", required=True)
    parser.add_argument("-c", "--category", help="Category for query.", required=True)
    args = parser.parse_args()
    # to search 
    query = args.query
    logger = GPLogger("Google News DataPump")

    urllib3.disable_warnings()

    netowl_key = 'netowl ff5e6185-5d63-459b-9765-4ebb905affc8'
    geoevent_endpoint = r'https://wdcrealtimeevents.esri.com:6143/geoevent/rest/receiver/ca-query-in'
    temp_directory = r'/Users/jame9353/Documents/temp_data/NetOwl/text'

    downloaded_urls = []

    count = 0

    logger.info('Start Querying Google News...')

    while True:

        logger.info("Querying Google News for: {}".format(query))
  
        for j in search_news(query, tld="com", num=int(args.max), stop=10, pause=2):
            logger.debug("Getting Data From: {}".format(j))
            if j not in downloaded_urls:    
                downloaded_urls.append(j)
                logger.debug("{0} has not been downloaded, beginning processing.".format(j))
                count +=1
                try:
                    r = requests.get(j)
                    
                    soup = BeautifulSoup(r.content, features="lxml")
                    soup_list = [s.extract() for s in soup(['style', 'script', '[document]', 'head', 'title'])]
                    visible_text = soup.getText()

                    filename = args.query.replace(" ", "_") + str(count)
                    text_file_path = os.path.join(temp_directory, filename + '.txt')
                    with open(text_file_path, 'w') as text_file:
                        text_file.write(visible_text)
                        text_file.close()
                    
                    logger.debug("{0} has been downloaded, passing data to NetOwl API.".format(j))

                    netowl_curl(text_file_path, temp_directory, ".json", netowl_key)
                    logger.debug("{0} successfully processed through NetOwl API.".format(j))

                    with open(text_file_path + ".json", 'rb') as json_file:
                        data = json.load(json_file)

                        entity_list, links_list, events_list = process_netowl_json(filename, data, j, query, args.category)
                        logger.debug("{0} entities extracted from {1}".format(str(len(entity_list)), j))
                        doc_entities = []
                        for entity in entity_list:
                            if entity.geo_entity == True:
                                if entity.geo_type == 'coordinate' or entity.geo_type == 'address' or entity.geo_subtype == 'city':
                                    doc_entities.append(vars(entity))


                        #logger.info(doc_entities)
                        post_to_geoevent(json.dumps(doc_entities), geoevent_endpoint)
                        logger.debug("{0} spatial entities passed to {1}".format(str(len(doc_entities)), geoevent_endpoint))

                    os.remove(text_file_path)
                    os.remove(text_file_path + ".json")

                
                except Exception as e:
                    logger.error("Unable to query data from {0}, skipping.".format(j, e))

        logger.info("Finished processing of {0}, sleeping for {1} seconds".format(query, "300"))
        time.sleep(300)
if __name__=="__main__":    
    main()