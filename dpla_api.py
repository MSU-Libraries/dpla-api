"""Access DPLA api and work with data."""
from __future__ import division
from dpla.api import DPLA
from lxml import etree
import ConfigParser
from metadpla import DplaMetadata
from hathi import HathiBibApi
import codecs
import time
import json
import math
import os


class DplaApi():
    """Interact with DPLA API using pre-acquired key."""

    def __init__(self):
        """Load DPLA key and establish connection."""
        self.dpla_key = self.__load_dpla_key()
        self.dpla = DPLA(self.dpla_key)
        self.result = None
        self.metadata_records = []

    def search(self, q_value, page_size=100):
        """Run basic search query across DPLA.

        args:
            q_value (str) -- value to search
        kwargs:
            page_size (int) -- max number of results to request from DPLA.
            (DPLA-imposed limit is 500)
        """
        if isinstance(q_value, str):
            self.query = q_value.strip().replace(",", "").replace("(", "").replace(")", "")
            self.result = self.dpla.search(q=q_value, page_size=page_size)
        elif isinstance(q_value, dict):
            self.query = q_value
            self.result = self.dpla.search(searchFields=q_value, page_size=page_size)

        print "Query: '{0}' returned {1} results".format(self.query, self.result.count)
        time.sleep(.5)
        self.all_returned_items = self.result.items
        if self.result.count > self.result.limit:
            pages = int(math.ceil(self.result.count / self.result.limit))
            for page in range(2, pages + 1):
                print "----Accessing results page {0}".format(page)
                self.result = self.dpla.search(q=q_value, page_size=page_size, page=page)
                self.all_returned_items += self.result.items
                time.sleep(.5)

    def build_arc_rdf_dataset(self, check_match=True, disciplines="", id_match=None):
        """Iterate over search results and pull necessary elements to create ARC RDF.

        Store results in a list of python dictionaries.
        kwargs:
            check_match(bool): check if RDF for item has already been created.
            disciplines(str): string of "|"-separated values.
        """
        self.disciplines = disciplines
        self.id_match = id_match
        if check_match:
            self.__load_match_data()

        print "----Check: {0} records transferred"\
              .format(len(self.all_returned_items))
        rdf_matches = 0
        new_records = 0
        for item in self.all_returned_items:
            if check_match:
                if os.path.basename(item["@id"]) in self.existing_records:
                    rdf_matches += 1
                else:
                    self.__process_metadata(item)
                    self.existing_records.append(item["@id"])
                    new_records += 1

            else:
                self.__process_metadata(item)

        # print "----Found: {0} existing RDF records".format(rdf_matches)
        # print "----Saved: {0} new metadata records".format(new_records)
        self.__load_match_data(reset_match_file=True)
        self._store_match_data()

    def create_tsv(self, records=None,
                   output_path="data/radicalism-dpla.tsv"):
        """Build TSV file for ARC pre-RDF dataset.

        kwargs:
            records(list): by default, the results created from the current search.
        """
        if not records:
            records = self.metadata_records
        tsv_lines = []
        headings = "\t".join(records[0].keys())
        headings += "\n"
        lists = 0
        tsv_lines.append(headings)
        for record in records:
            line = ""
            for key, value in record.items():
                if isinstance(value, list):
                    if any(isinstance(v, list) for v in value):
                        lists += 1
                    else:
                        line += " | ".join([v.replace("\t", " ") for v in value if v is not None])
                elif isinstance(value, str):
                    line += value.replace("\t", " ")
                else:
                    value_str = json.dumps(value)
                    line += value_str
                line += "\t"
            line += "\n"
            tsv_lines.append(line)

        with codecs.open(output_path, "w", "UTF-8") as output_file:
            for line in tsv_lines:
                output_file.write(line)

        print "Completed writing {0}".format(output_path)

    def update_rdf_registry(self, rdf_dir="rdf", reset_matches=False):
        """Update listings of already-processed items.

        kwargs:
            rdf_dir(str): directory in which to find rdf.
            reset_matches(bool): reset match list and rebuild from scratch,
                based entirely on RDF files present in specified dir. Any
                records added to the registry through querying will be removed.
        """
        self.__load_match_data(reset_match_file=reset_matches)
        update_count = 0
        match_count = 0
        for root, dirs, files in os.walk(rdf_dir):
            for f in files:
                if f.endswith(".xml"):
                    root_name = os.path.splitext(f)[0]
                    if root_name not in self.existing_records:
                        self.existing_records.append(root_name)
                        update_count += 1
                    else:
                        match_count += 1
        print "Matching records: {0}".format(match_count)
        print "New records: {0}".format(update_count)
        self._store_match_data()

    def _store_match_data(self):
        """Store updated processed item list."""
        with open(self.match_file, "w") as match_file:
            json.dump(self.existing_records, match_file)

    def __load_dpla_key(self):
        """Load DPLA API Key from config file."""
        config = ConfigParser.RawConfigParser()
        config.read("default.cfg")
        return config.get("dpla_api", "api_key")

    def __load_match_data(self, reset_match_file=False):
        """Prepare data on previous search results."""
        self.match_file = self.__load_match_settings()
        if reset_match_file is True:
            self.existing_records = []
        else:
            self.existing_records = json.load(open(self.match_file, "r"))

    def __load_match_settings(self):
        """Load file containing list of all previously processed items."""
        config = ConfigParser.RawConfigParser()
        config.read("default.cfg")
        return config.get("check_match", "match_file")

    def __process_metadata(self, item):
        """Process metadata from JSON DPLA record, pulling descriptive
        elements from the 'sourceResource' fields.

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
        d_metadata.record["discipline"] = self.disciplines
        # d_metadata.record["genre"] = self._get_genre_from_marc(item)
        d_metadata.record["genre"] = "none"
        d_metadata.record["archive"] = ""
        d_metadata.record["role"] = ""
        d_metadata.record["federation"] = "SiRO"
        d_metadata.record["original_query"] = self.query
        d_metadata.record["id"] = item["@id"]
        if self.id_match:
            if self.id_match in d_metadata.record["seeAlso"]:
                self.metadata_records.append(d_metadata.record)
        else:
            self.metadata_records.append(d_metadata.record)

    def _get_genre_from_marc(self, item):
        """Check for 'literary form' value in MARC record.

        args:
            item (dict): Python dictionary from JSON results of DPLA search.
        returns:
            (str) genre value(s) to include in output.
        """
        genre_value = "none"
        value_map = {"0": "Nonfiction",
                     "1": "Fiction",
                     "d": "Drama",
                     "e": "Nonfiction",
                     "f": "Fiction",
                     "i": "Correspondence",
                     "j": "Fiction",
                     "p": "Poetry"
                     }
        """
        This method could be used with DPLA-returned MARC info, if the spacing
        of the 008 field was preserved.
        if self._marc_record(item):
            for field in item["originalRecord"]["controlfield"]:
                if field["tag"] == "008" and len(field["#text"]) > 33:
                    genre = field["#text"][33]
                    genre_value = value_map.get(genre, "")
        """
        # Access bibliographic information via the HathiTrust API.
        if "hathitrust" in item.get("isShownAt", ""):
            record = self._get_hathi_record(item)
            # print record
            marc_string = record["records"][str(self.hathi_id)]["marc-xml"]
            genre = self._extract_genre(marc_string)
            genre_value = value_map.get(genre, "")

        return genre_value

    def _extract_genre(self, marc_string):
        """Extract appropriate byte-mark in 008 to indicate genre.

        args:
            marc_string(str): marc xml as string.
        """
        path_008 = "/collection/record/controlfield[@tag='008']"
        tree = etree.fromstring(marc_string.encode("utf-8"))
        text_008 = tree.xpath(path_008)[0].text
        if len(text_008) > 33:
            genre = text_008[33]
        else:
            genre = "null"
        return genre

    def _get_hathi_record(self, item):
        """Get HathiTrust record.

        args:
            item (dict): Python dictionary from JSON results of DPLA search.
        """
        self.hathi_id = item["originalRecord"]["_id"]
        hbi = HathiBibApi()
        return hbi.get_record(self.hathi_id)

    def _marc_record(self, item):
        """Check if item contains a MARC record.

        args:
            item(dict): Python dictionary from JSON results of DPLA search.
        returns:
            is_marc(bool): true if item contains a marc record, false otherwise.
        """
        is_marc = False
        if "originalRecord" in item:
            if "controlfield" in item["originalRecord"]:
                is_marc = True
        return is_marc

    # Not using these anymore, might not work.
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

