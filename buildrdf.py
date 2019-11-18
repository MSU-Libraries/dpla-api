"""Build individual RDF XML records from spreadsheet rows."""
import os
from lxml import etree
import re
import codecs


class BuildRdf():
    """Class to build RDF according to ARC standard."""

    def __init__(self, archive="dpla"):
        """Load default values."""
        self.default_values = {
            "discipline": ["History"],
            "role": ["CRE"],
            "archive": archive,
            "genre": ["Unspecified"],
            "freeculture": ["TRUE"]
        }
        self.ns_map = {
            "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
            "role": "http://www.loc.gov/loc.terms/relators/",
            "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
            "collex": "http://www.collex.org/schema#",
            "dcterms": "http://purl.org/dc/terms/",
            "dc": "http://purl.org/dc/elements/1.1/",
            "sro": "http://www.lib.msu.edu/sro/schema#",
        }
        self.file_count = 0

    def __set_rdf_root(self):
        """Set or reset RDF root to rebegin new file."""
        self.rdf_root = etree.Element("{{{0}}}RDF".format(self.ns_map["rdf"]), nsmap=self.ns_map)

    def build_rdf_from_tsv(self, tsv_path, output_path, lines_to_process=None, records_per_file=500):
        """Initialize processing of tsv file.

        args:
        tsv_path (str) -- path to tsv file.
        lines_to_process (int) -- allow user to determine number of lines in tsv to process.
        """
        self.records_per_file = records_per_file
        self.output_path = output_path
        self.lines_to_process = lines_to_process
        self.tsv_path = tsv_path

        # Array of columns in the order they appear in the standard pre-RDF tsv file.
        """
        column_alignment = ["discipline", "federation", "language", "creator", "id"
                            "title", "archive", "genre", "freeculture", "original_query", "subjects",
                            "date", "type", "thumbnail", "seeAlso"]
        """
        self.__set_rdf_root()

        if self.__check_file():
            self.__read_tsv()
            self.__write_rdf()
            print("Processed {0} records".format(self.lines_processed))

        else:
            print("Invalid path -- File Doesn't Exist: {0}".format(self.tsv_path))

    def __read_tsv(self):
        """Open and read file."""
        with codecs.open(self.tsv_path, "r", "utf-8") as tsv_file:

            if not self.lines_to_process:
                self.lines_to_process = len(tsv_file.readlines())

            print("Processing {0} records...".format(self.lines_to_process - 1))

            # The previous readlines() call moved the pointer to the end of the file, making iteration
            # impossible. This line resets the pointer.
            tsv_file.seek(0)

            # Skip first line (headings)
            self.headings = [h.strip() for h in tsv_file.readline().split("\t")]
            self.lines_processed = 0
            for line in tsv_file:
                if self.lines_to_process > self.lines_processed:
                    rdf = self.__process_line(line)
                    self.rdf_root.append(rdf)
                    self.lines_processed += 1

    def __write_rdf(self):
        """Write all RDF processed up to the current line."""
        if self.file_count > 0:
            output_parts = os.path.splitext(self.output_path)
            output_path = output_parts[0] + "_{0}".format(self.file_count) + output_parts[1]
        else:
            output_path = self.output_path

        with codecs.open(output_path, "w", "utf-8") as output_file:
            output_file.write(etree.tostring(self.rdf_root, encoding="unicode", pretty_print=True))

        self.file_count += 1
        self.__set_rdf_root()

    def __process_line(self, line):
        """Process individual line of tsv file.

        args:
        line (str) -- single line from tsv file.
        """
        self.line_data = line.split("\t")
        self.line_reference = {}
        self.line_reference.update(zip(self.headings, self.line_data))

        if self.lines_processed % self.records_per_file == 0 and self.lines_processed != 0:
            self.__write_rdf()
            print("Processed {0} records".format(self.lines_processed))

        """
        print "{0} : {1}".format(
            self.line_reference["id"].encode("ascii", errors="ignore"),
            self.line_reference["title"].encode("ascii", errors="ignore"))
        """

        return self.__create_rdf()

    def __create_rdf(self):
        """Start RDF creation."""

        self.ns_map = {
            "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
            "role": "http://www.loc.gov/loc.terms/relators/",
            "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
            "collex": "http://www.collex.org/schema#",
            "dcterms": "http://purl.org/dc/terms/",
            "dc": "http://purl.org/dc/elements/1.1/",
            "sro": "http://www.lib.msu.edu/sro/schema#",
        }

        # self.rdf_root = etree.Element("{{{0}}}RDF".format(self.ns_map["rdf"]), nsmap=self.ns_map)
        return self.__process_elements()

    def __process_elements(self):
        """Process data into RDF."""
        # The triple-{} includes a literal "{}" and a {} that operates the format string.
        # That is, one escapes braces in a format string by doubling them.
        self.siro_wrapper = etree.Element("{{{0}}}{1}".format(self.ns_map["sro"], self.default_values["archive"]))
        siro_wrapper_attribute = "{{{0}}}about".format(self.ns_map["rdf"])
        self.siro_wrapper.attrib[siro_wrapper_attribute] = self.line_reference["id"]
        self.__add_subelement(self.siro_wrapper, "federation", "collex", field_value="SiRO")

        for value in self.__get_values("archive"):
            self.__add_subelement(self.siro_wrapper, "archive", "collex", field_value=value)

        self.__add_subelement(self.siro_wrapper, "title", "dc", field_value=self.line_reference["title"])
        self.__add_creators()
        self.__add_subelement(self.siro_wrapper, "source", "dc", field_value=self.line_reference["source"])
        try:
            self.__add_subelement(
                self.siro_wrapper,
                "description", "dc",
                field_value="\n".join([d.strip(":").strip() for d in self.line_reference["description"].split("|")])
            )
        except KeyError as keye:
            pass

        for subject in self.line_reference["subjects"].split("|"):
            self.__add_subelement(self.siro_wrapper, "subject", "dc", field_value=subject.strip())

        for value in self.__get_values("discipline"):
            self.__add_subelement(self.siro_wrapper, "discipline", "collex", field_value=value)

        self.__add_genres()
        self.__add_freecultures()
        self.__add_type()
        self.__add_date()

        self.__add_subelement(self.siro_wrapper, "fulltext", "collex", field_value="TRUE")
        if self.line_reference["language"].strip():
            self.__add_subelement(self.siro_wrapper, "language", "dc", field_value=self.line_reference["language"])

        if self.line_reference.get("seeAlso", "").strip():
            object_link = self.line_reference["seeAlso"].strip()
        elif self.line_reference["see_also"].strip():
            object_link = self.line_reference["see_also"].strip()
        else:
            object_id = os.path.basename(self.line_reference["id"])
            object_link = "http://dp.la/item/{0}".format(object_id)

        self.__add_subelement(
            self.siro_wrapper, "seeAlso", "rdfs",
            attributes={"{{{0}}}resource".format(self.ns_map["rdf"]): object_link}
        )

        if self.line_reference["thumbnail"].strip():
            self.__add_subelement(self.siro_wrapper, "thumbnail", "collex", attributes={"{{{0}}}resource".format(self.ns_map["rdf"]): self.line_reference["thumbnail"]})

        return self.siro_wrapper
        """
        with codecs.open("rdf/20170616/{0}.xml".format(os.path.basename(self.line_reference["id"])), "w", "utf-8") as output_file:
            output_file.write(etree.tostring(self.rdf_root, encoding="unicode", pretty_print=True))
        """

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
        if "creator" in self.line_reference:

            if self.line_reference["creator"].strip():
                self.creators = self.line_reference["creator"].split("|")
            else:
                self.creators = ["Unknown"]
            self.role_type = self.__get_role()
            creator_roles = zip(self.role_type, self.creators)
        elif "creators" in self.line_reference:
            creator_roles = []
            for creator_entry in self.line_reference["creators"].split("|"):
                creator, role = creator_entry.split(":")
                creator_roles.append((role.strip(), creator.strip()))

        for creator in creator_roles:
            self.__add_subelement(self.siro_wrapper, creator[0], "role", field_value=creator[1].strip())

    def __add_genres(self):
        """Add genres from tsv, from default, or based on heuristic."""
        if self.line_reference["genre"] == "none":
            self.genres = []
        else:
            self.genres = [g.title() for g in self.line_reference["genre"].split("|")]

        self.letter_pattern = r'\[.*[Ll]etter.*\]'
        if re.search(self.letter_pattern, self.line_reference["title"]):
            self.genres.append("Correspondence")

        if len(self.genres) == 0:
            self.genres += self.default_values["genre"]

        for genre in set(self.genres):
            self.__add_subelement(self.siro_wrapper, "genre", "collex", field_value=genre)

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
            record_type = self.line_reference["type"].title()

        self.__add_subelement(self.siro_wrapper, "type", "dc", field_value=record_type)

    def __add_freecultures(self):
        # Generate freeculture field.

        if self.line_reference.get("freeculture", "") == "":
            self.freecultures = ["TRUE"]

        else:
            self.freecultures = [self.line_reference["freeculture"]]

        for freeculture in set(self.freecultures):
            self.__add_subelement(self.siro_wrapper, "freeculture", "collex", field_value=freeculture)

    def __add_date(self):
        """Heuristic for date handling."""
        date = self.line_reference["date"]
        if "|" in date:
            date = date.split("|")[0]
        dcdate = None

        matches = re.findall(r'[0-9]{4}', date)

        if re.search(r'^[0-9]{4}$', date):
            dcdate = date

        elif matches:
            date_label = date
            if min(matches) != max(matches):
                date_value = ",".join([min(matches), max(matches)])
            else:
                date_value = min(matches)  # Arbitrarily choose one over the other if they are the same.

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
            self.__add_subelement(
                collex_date_wrapper,
                "label", "rdfs", field_value=date_label
            )
            self.__add_subelement(
                collex_date_wrapper,
                "value", "rdf", field_value=date_value
            )

    def __get_role(self):
        """Check for role value in tsv data, use default if blank."""
        if not self.line_reference["role"].strip():
            return ["CRE"] * len(self.creators)
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
