from dpla.api import DPLA
from pprint import pprint
from lxml import etree


class DplaApi():
    def __init__(self, dpla_key="07c4dfca29876f8b591732735913abb4"):
        self.dpla_key=dpla_key
        self.dpla = DPLA(dpla_key)
        self.result = None

    def search(self, q_value, page_size=100):
        self.result = self.dpla.search(q=q_value, page_size=page_size)
        print "===First Result==="
        print "---Access [instance].result.items object to see all---"
        pprint(self.result.items[0])

    def return_marcxml(self):
        if self.result is None:
            print "Error -- No data available -- Run search first"
            return

        for item in self.result.items:
            json_record = item["originalRecord"]
            self.build_marcxml_record(json_record)

    def build_marcxml_record(self, json_record):
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




