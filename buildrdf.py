"""Build individual RDF XML records from spreadsheet rows."""
import os
from lxml import etree
import re
import codecs


class BuildRdf():
    """Class to build RDF according to ARC standard."""

    def __init__(self):
        """Load default values."""
        self.default_values = {
            "discipline": ["History"],
            "role": ["CRE"],
            "archive": ["dpla"],
            "genre": ["Nonfiction"],
        }

    def build_rdf_from_tsv(self, tsv_path, lines_to_process=None):
        """Initialize processing of tsv file.

        args:
        tsv_path (str) -- path to tsv file.
        lines_to_process (int) -- allow user to determine number of lines in tsv to process.
        """
        self.lines_to_process = lines_to_process
        self.tsv_path = tsv_path

        # Array of columns in the order they appear in the standard pre-RDF tsv file.
        """
        column_alignment = ["discipline", "federation", "language", "creator", "id"
                            "title", "archive", "genre", "original_query", "subjects",
                            "date", "type", "thumbnail", "seeAlso"]
        """
        if self.__check_file():
            self.__read_tsv()

        else:
            print "Invalid path -- File Doesn't Exist: {0}".format(self.tsv_path)

    def __read_tsv(self):
        """Open and read file."""
        with codecs.open(self.tsv_path, "r", "utf-8") as tsv_file:

            if not self.lines_to_process:
                self.lines_to_process = len(tsv_file.readlines())

            print "Processing {0} records...".format(self.lines_to_process)

            # The previous readlines() call moved the pointer to the end of the file, making iteration
            # impossible. This line resets the pointer.
            tsv_file.seek(0)

            # Skip first line (headings)
            self.headings = [h.strip() for h in tsv_file.readline().split("\t")]
            self.lines_processed = 0
            for line in tsv_file:
                if self.lines_to_process > self.lines_processed:
                    self.__process_line(line)
                    self.lines_processed += 1

    def __process_line(self, line):
        """Process individual line of tsv file.

        args:
        line (str) -- single line from tsv file.
        """
        self.line_data = line.split("\t")
        self.line_reference = {}
        self.line_reference.update(zip(self.headings, self.line_data))
        if self.lines_processed % 500 == 0:
            print "Processed {0} records".format(self.lines_processed)
        # print "{0} : {1}".format(self.line_reference["id"].encode("ascii", errors="ignore"), self.line_reference["title"].encode("ascii", errors="ignore"))
        self.__create_rdf()

    def __create_rdf(self):
        """Start RDF creation."""

        self.ns_map = {
                    "rdf":"http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                    "role":"http://www.loc.gov/loc.terms/relators/",
                    "rdfs":"http://www.w3.org/2000/01/rdf-schema#",
                    "collex":"http://www.collex.org/schema#",
                    "dcterms":"http://purl.org/dc/terms/",
                    "dc":"http://purl.org/dc/elements/1.1/",
                    "sro":"http://www.lib.msu.edu/sro/schema#",
                    }

        self.rdf_root = etree.Element("{{{0}}}RDF".format(self.ns_map["rdf"]), nsmap=self.ns_map)
        self.__process_elements()

    def __process_elements(self):
        """Process data into RDF."""
        # The triple-{} includes a literal "{}" and a {} that operates the format string.
        # That is, one escapes braces in a format string by doubling them.
        self.siro_wrapper = self.__add_subelement(self.rdf_root, "dpla", "sro", attributes={"{{{0}}}about".format(self.ns_map["rdf"]): self.line_reference["id"]})
        federation = self.__add_subelement(self.siro_wrapper, "federation", "collex", field_value="SiRO")
        

        for value in self.__get_values("archive"):
            archive = self.__add_subelement(self.siro_wrapper, "archive", "collex", field_value=value)
        
        title = self.__add_subelement(self.siro_wrapper, "title", "dc", field_value=self.line_reference["title"])
        self.__add_creators()
        source = self.__add_subelement(self.siro_wrapper, "source", "dc", field_value=self.line_reference["source"])
        
        for subject in self.line_reference["subjects"].split("|"):
            subject = self.__add_subelement(self.siro_wrapper, "subject", "dc", field_value=subject.strip())

        for value in self.__get_values("discipline"):
            archive = self.__add_subelement(self.siro_wrapper, "discipline", "collex", field_value=value)
        
        self.__add_genres()
        self.__add_type()
        self.__add_date()

        fulltext = self.__add_subelement(self.siro_wrapper, "fulltext", "collex", field_value="TRUE")
        if self.line_reference["language"].strip():
            language = self.__add_subelement(self.siro_wrapper, "language", "dc", field_value=self.line_reference["language"])
        
        if self.line_reference["seeAlso"].strip():
            object_link = self.line_reference["seeAlso"]
        else:
            object_id = os.path.basename(self.line_reference["id"])
            object_link = "http://dp.la/item/{0}".format(object_id)

        see_also = self.__add_subelement(self.siro_wrapper, "seeAlso", "rdfs", attributes={"{{{0}}}resource".format(self.ns_map["rdf"]): object_link})

        if self.line_reference["thumbnail"].strip():
            thumbnail = self.__add_subelement(self.siro_wrapper, "thumbnail", "collex", attributes={"{{{0}}}resource".format(self.ns_map["rdf"]): self.line_reference["thumbnail"]})

        #print type(etree.tostring(self.rdf_root, xml_declaration=True, encoding="UTF-8", pretty_print=True))
        with codecs.open("rdf/20170616/{0}.xml".format(os.path.basename(self.line_reference["id"])), "w", "utf-8") as output_file:
            output_file.write(etree.tostring(self.rdf_root, encoding="unicode", pretty_print=True))


    def __get_values(self, field):
        """
        Check for values in tsv data, return defaults otherwise.

        args:
        field (str) -- field name from heading of tsv file.
        """
        if not self.line_reference[field].strip():
            return self.default_values[field]

        else:
            return [value.strip() for value in self.line_reference[field].split("|")]

    def __add_creators(self):
        """Bring together roles and creators."""
        if self.line_reference["creator"].strip():
            self.creators = self.line_reference["creator"].split("|")
        else:
            self.creators = ["Unknown"]
        self.role_type = self.__get_role()
        creator_roles = zip(self.role_type, self.creators)
        for creator in creator_roles:
            role = self.__add_subelement(self.siro_wrapper, creator[0], "role", field_value=creator[1].strip())

    def __add_genres(self):
        """Add genres from tsv, from default, or based on heuristic."""
        if self.line_reference["genre"] == "none":
            self.genres = []
        else:
            self.genres = [self.line_reference["genre"]]

        self.letter_pattern = r'\[.*[Ll]etter.*\]'
        if re.search(self.letter_pattern, self.line_reference["title"]):
            self.genres.append("Correspondence")

        if len(self.genres) == 0:
            self.genres += self.default_values["genre"]

        for genre in set(self.genres):
            genre_field = self.__add_subelement(self.siro_wrapper, "genre", "collex", field_value=genre)

    def __add_type(self):
        """Find 1 type for each item."""

        manuscript_pattern = r'\[.*[Mm]anuscript.*\]'
        if re.search(manuscript_pattern, self.line_reference["title"]):
            record_type = "Manuscript"

        elif self.line_reference["type"] == "image":
            record_type = "Still Image"

        elif self.line_reference["type"] == "text" and re.search(self.letter_pattern, self.line_reference["title"]):
            record_type = "Manuscript"

        elif self.line_reference["type"] == "text":
            record_type = "Codex"

        else:
            record_type = "Codex"

        rtype = self.__add_subelement(self.siro_wrapper, "type", "dc", field_value=record_type)

    def __add_date(self):
        """Heuristic for date handling."""
        date = self.line_reference["date"]
        dcdate = None

        matches = re.findall(r'[0-9]{4}', date)

        if re.search(r'^[0-9]{4}$', date):
            dcdate = date

        elif matches:
            date_label = date
            date_value = ",".join([min(matches), max(matches)])

        elif date.strip():
            date_label = date
            date_value = "Uncertain"

        else:
            dcdate = "Uncertain"

        if dcdate:
            date_field = self.__add_subelement(self.siro_wrapper, "date", "dc", field_value=dcdate)

        else:
            date_field = self.__add_subelement(self.siro_wrapper, "date", "dc")
            collex_date_wrapper = self.__add_subelement(date_field, "date", "collex")
            rdf_date_label = self.__add_subelement(collex_date_wrapper,
                                                   "label", "rdfs", field_value=date_label)
            rdf_date_label = self.__add_subelement(collex_date_wrapper,
                                                   "value", "rdf", field_value=date_value)

    def __get_role(self):
        """Check for role value in tsv data, use default if blank."""
        if not self.line_reference["role"].strip():

            return ["CRE"]*len(self.creators)
        else:
            return [role.strip() for role in self.line_reference["role"].split("|")]

    def __add_subelement(self, parent, tag_name, prefix, field_value=None, attributes=None):
        """

        """
        subelement = etree.SubElement(parent, "{{{0}}}{1}".format(self.ns_map[prefix], tag_name))
        if attributes is not None:
            for key, value in attributes.items():
                subelement.attrib[key] = value

        if field_value is not None:
            subelement.text = field_value

        return subelement

    def __check_file(self):
        """Check to make sure tsv file exists."""
        return os.path.exists(self.tsv_path)
