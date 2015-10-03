from __future__ import division
from dpla.api import DPLA
from pprint import pprint
from lxml import etree
import ConfigParser
from metadpla import DplaMetadata
import codecs
import time
import json
import math


class DplaApi():
    """Interact with DPLA API using pre-acquired key."""
    def __init__(self):
        self.dpla_key= self.__load_dpla_key()
        self.dpla = DPLA(self.dpla_key)
        self.result = None
        self.metadata_records = []

    def search(self, q_value, page_size=100):
        """
        Run basic search query across DPLA.
        q_value (str) -- value to search
        page_size (int) -- max number of results to request from DPLA. (DPLA-imposed limit is 500)
        """
        self.query = q_value
        print "Query: {0}".format(self.query)
        self.result = self.dpla.search(q=q_value, page_size=page_size)
        time.sleep(.5)
        self.all_returned_items = self.result.items
        if self.result.count > self.result.limit:
            pages = int(math.ceil(self.result.count / self.result.limit))
            for page in range(2, pages + 1):
                print "----Accessing results page {0}".format(page)
                self.result = self.dpla.search(q=q_value, page_size=page_size, page=page)
                self.all_returned_items += self.result.items
                time.sleep(.5)

        


    def build_arc_rdf_dataset(self, check_match=True):
        """Iterate over search results and pull necessary elements to create ARC RDF, storing them in a list of python dictionaries."""

        if check_match:
            self.__load_match_data()

        print "Query '{0}' returned {1} records (Check: {2} records transferred)".format(self.query, self.result.count, len(self.all_returned_items))

        for item in self.all_returned_items:

            if check_match:
                if item["@id"] in self.existing_records:
                    pass
                else:
                    self.__process_metadata(item)
                    self.existing_records.append(item["@id"])

            else:
                self.__process_metadata(item)

        

    def create_tsv(self, output_path="data/radicalism-all-dpla.tsv"):
        """Build CSV file for ARC pre-RDF dataset."""
        tsv_text = ""
        headings = "\t".join(self.metadata_records[0].keys())
        tsv_text += headings + "\n"
        for record in self.metadata_records:
            for key, value in record.items():
                if isinstance(value, list):
                    tsv_text += " | ".join(value) 
                else:
                    tsv_text += value
                tsv_text += "\t"
            tsv_text += "\n"

        with codecs.open(output_path, "w", "UTF-8") as output_file:
            output_file.write(tsv_text)

        print "Completed writing {0}".format(output_file)


    def return_marcxml(self):
        if self.result is None:
            print "Error -- No data available -- Run search first"
            return

        for item in self.items:
            json_record = item["originalRecord"]
            xml = self.build_marcxml_record(json_record)
            if xml is not None:
                with open(os.path.join(output_path, str(item["id"]))+".xml", "w") as f:
                    f.write(etree.tostring(xml, encoding="utf-8", xml_declaration=True))
                xml_processed += 1
            else:
                errors += 1

        print "{0} Errors Returned".format(errors)
        print "{0} XML Files Written".format(xml_processed)
        print "{0} Non Standard Records".format(self.non_standard_records)
        print "{0} MARC Namespace Records".format(self.marc_namespace)

    def build_marcxml_record(self, json_record):

        root = None
        if "leader" not in json_record and "metadata" not in json_record:
            self.non_standard_records += 1
            #print "\n================Non Standard Record===============\n"
            #print json_record
            return None

        elif "metadata" in json_record:

            if "marc:record" in json_record["metadata"]:
                self.marc_namespace += 1
                json_record = json_record["metadata"]["marc:record"] 
                try:
                    root = etree.Element("record", xmlns="http://www.loc.gov/MARC21/slim")
                    leader = etree.SubElement(root, "leader")
                    leader.text = json_record["marc:leader"]
                    for c in json_record["marc:controlfield"]:
                        controlfield = etree.SubElement(root, "controlfield", tag=c["tag"])
                        controlfield.text = c["#text"]
                    for d in json_record["marc:datafield"]:
                        datafield = etree.SubElement(root, "datafield", tag=d["tag"], ind1=d["ind1"], ind2=d["ind2"])
                        # When there's only one subfield, d["subfield"] will return a dict. Otherwise, a list of dicts.
                        if isinstance(d["marc:subfield"], dict):
                            subfield = etree.SubElement(datafield, "subfield", code=d["marc:subfield"]["code"])
                            subfield.text = d["marc:subfield"]["#text"]
                        else:
                            for s in d["marc:subfield"]:
                                subfield = etree.SubElement(datafield, "subfield", code=s["code"])
                                subfield.text = s["#text"]
                except Exception as e:
                    
                    print "\n================Error In Record===============\n"
                    print e
                    print json_record
                    return None

        elif "leader" in json_record:

            try:
                root = etree.Element("record", xmlns="http://www.loc.gov/MARC21/slim")
                leader = etree.SubElement(root, "leader")
                leader.text = json_record["leader"]
                for c in json_record["controlfield"]:
                    controlfield = etree.SubElement(root, "controlfield", tag=c["tag"])
                    controlfield.text = c["#text"]
                for d in json_record["datafield"]:
                    datafield = etree.SubElement(root, "datafield", tag=d["tag"], ind1=d["ind1"], ind2=d["ind2"])
                    # When there's only one subfield, d["subfield"] will return a dict. Otherwise, a list of dicts.
                    if isinstance(d["subfield"], dict):
                        subfield = etree.SubElement(datafield, "subfield", code=d["subfield"]["code"])
                        subfield.text = d["subfield"]["#text"]
                    else:
                        for s in d["subfield"]:
                            subfield = etree.SubElement(datafield, "subfield", code=s["code"])
                            subfield.text = s["#text"]
            except Exception as e:
                
                print "\n================Error In Record===============\n"
                print e
                print json_record
                return None

        return root
        """
        # Changes from lib computer. For future review.
        root = etree.Element("record", xmlns="http://www.loc.gov/MARC21/slim")
        leader = etree.SubElement(root, "leader")
        leader.text = json_record["leader"]
        for c in json_record["controlfield"]:
            controlfield = etree.SubElement(root, "controlfield", tag=c["tag"])
            controlfield.text = c["#text"]

            for row in q_datafields:
                datafield = etree.SubElement(root,"datafield",tag=row.tag,ind1=row.ind1,ind2=row.ind2)
                q_subfields = Subfields.objects.using("metagds").filter(datafield=row.datafield_id)
                for sub_row in q_subfields:
                    subfield = etree.SubElement(datafield,"subfield",code=sub_row.code)
                    subfield.text = sub_row.content
        """

    def return_html(self, filepath="dpla.html"):
        with open(filepath, "w") as f:
            f.write("<table border='1' style='100%'>")
            f.write("<tr>")
            f.write("<td>Title</td>")
            f.write("<td>Link</td>")
            f.write("</tr>")
            for item in result.items:
                title = item["sourceResource"]["title"]
                url = unicode(item["isShownAt"])
                if isinstance(title, list):
                    title_clean = unicode(title[0])

                else:
                    title_clean = unicode(title)

                f.write("<tr>")
                f.write("<td>"+title_clean.encode("UTF-8")+"</td>")
                f.write("<td><a href='"+url+"'>"+url+"</td>")
                f.write("<tr>")
            f.write("</table>")

    def __load_dpla_key(self):
        """Load DPLA API Key from config file."""
        config = ConfigParser.RawConfigParser()
        config.read("default.cfg")
        return config.get("dpla_api", "api_key")

    def __load_match_data(self):
        """Prepare data on previous search results."""
        match_file, reset_match_file = self.__load_match_settings()
        if reset_match_file == "true":
            self.existing_records = []
        else:
            self.existing_records = json.load(open(match_file, "r"))

    def __load_match_settings(self):
        """Load file containing list of all previously processed items."""
        config = ConfigParser.RawConfigParser()
        config.read("default.cfg")
        return config.get("check_match", "match_file"), config.get("check_match", "reset_match_file")

    def __process_metadata(self, item):
        """Process metadata from JSON DPLA record, pulling descriptive elements from the 'sourceResource' fields.

        Positional arguments:
        item (dict) -- Python dictionary from JSON results of DPLA search.
        """
        d_metadata = DplaMetadata(item["sourceResource"])
        d_metadata.compile()
        d_metadata.record["thumbnail"] = item.get("object", "")
        d_metadata.record["seeAlso"] = item.get("isShownAt", "")
        if "provider" in item:
            d_metadata.record["source"] = item["provider"]["name"]
        elif "dataProvider" in item:
            d_metadata.record["source"] = item["dataProvider"]
        else:
            d_metadata.record["source"] = ""
        d_metadata.record["discipline"] = ""
        d_metadata.record["genre"] = ""
        d_metadata.record["archive"] = ""
        d_metadata.record["role"] = ""
        d_metadata.record["federation"] = "SiRO"
        d_metadata.record["original_query"] = self.query
        d_metadata.record["id"] = item["@id"]
        self.metadata_records.append(d_metadata.record)



