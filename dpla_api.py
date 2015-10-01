from __future__ import division
import math
from dpla.api import DPLA
from pprint import pprint
from lxml import etree
import os


class DplaApi():
    def __init__(self, dpla_key="07c4dfca29876f8b591732735913abb4"):
        self.dpla_key=dpla_key
        self.dpla = DPLA(dpla_key)
        self.items = None

    def search(self, q_value, page_size=100, get_all=True):
        result = self.dpla.search(q=q_value, page_size=page_size)
        self.items = result.items
        count = result.count
        if count > page_size and get_all:
            for i in range(2, int(math.ceil(count/page_size))+1, 1):
                result = self.dpla.search(q=q_value, page_size=page_size, page=i)
                self.items += result.items
        print "Returned {0} Items".format(len(self.items))

    def return_marcxml(self, output_path="/"):
        errors = 0
        xml_processed = 0
        self.non_standard_records = 0
        self.marc_namespace = 0

        if self.items is None:
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




