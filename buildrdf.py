import os
from lxml import etree

class BuildRdf():
    """class to build RDF according to ARC standard."""
    def __init__(self):
        pass


    def build_rdf_from_tsv(self, tsv_path):
        """
        Initialize processing of tsv file. 

        args:
        tsv_path (str) -- path to tsv file.
        """

        self.tsv_path = tsv_path

        #Array of columns in the order they appear in the standard pre-RDF tsv file.
        column_alignment = ["discipline", "federation", "language", "creator",
                            "title", "archive", "genre", "original_query", "subjects",
                            "date", "type", "thumbnail", "seeAlso"]

        if self.__check_file():
            self.__read_tsv()

        else:
            print "Invalid path -- File Doesn't Exist: {0}".format(self.tsv_path)

    def __read_tsv(self):
        """Open and read file."""
        with open(tsv_path, "r") as tsv_file:
            for line in tsv_file:
                self.__process_line(line)

    def __process_line(self, line):
        """Process individual line of tsv file.
        
        args:
        line (str) -- single line from tsv file.
        """
        self.line_data = line.split("\t")
        self.__create_rdf()

    def __create_rdf(self):
        """Start RDF creation."""

        self.ns_map = {
                    "rdf":"http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                    "role":"http://www.loc.gov/loc.terms/relators/",
                    "rdfs":"http://www.w3.org/2000/01/rdf-schema#",
                    "walters":"http://thedigitalwalters.org/schema#",
                    "collex":"http://www.collex.org/schema#",
                    "dcterms":"http://purl.org/dc/terms/",
                    "dc":"http://purl.org/dc/elements/1.1/",
                    }

        self.rdf_root = etree.Element("RDF", nsmap=self.ns_map)
        self.__process_elements()

    def __process_elements(self):
        """Process data into RDF."""
        self.__add_element(self.line_data[0])
        self.federation = self.line_data[1]
        self.language = 

    def __add_element(self):
        """

        """
        self.rdf_root.s

    def __check_file(self):
        """Check to make sure tsv file exists."""
        return os.path.exists(self.tsv_path)