from dpla.api import DPLA

dpla = DPLA("07c4dfca29876f8b591732735913abb4")
result = dpla.search(q="radicalism", page_size=500)

with open("radical-dpla.html", "w") as f:

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
