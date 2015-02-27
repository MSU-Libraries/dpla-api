from dpla.api import DPLA
from pprint import pprint


class DplaApi():
    def __init__(self, dpla_key="07c4dfca29876f8b591732735913abb4"):
        self.dpla_key=dpla_key
        self.dpla = DPLA(dpla_key)

    def search(self, q_value, page_size=100):
        self.result = self.dpla.search(q=q_value, page_size=page_size)
        print "===First Result==="
        print "---Access [instance].result.items object to see all---"
        pprint(self.result.items[0])

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




