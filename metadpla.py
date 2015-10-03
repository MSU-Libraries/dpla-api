

class DplaMetadata():

    def __init__(self, dpla_metadata):
        """
        Initialize object containing just the DPLA-level metadata (not from original record).

        Positional arguments:
        dpla_metadata (dict) -- object of "sourceResource"-level metadata. See dpla_sample_metadata.json for details.
        """
        self.metadata = dpla_metadata

    def compile(self):
        """Pull relevant metadata for ARC record, and record fields not found."""
        record = {

                        "date":"",
                        "title":"",
                        "subjects":[],
                        "type":[],
                        "creator":[],
                        "language":[],
                    }
        

        if "date" in self.metadata:
            if isinstance(self.metadata["date"], list):
                
                if "displayDate" in self.metadata["date"][0]:
                    record["date"] = self.metadata["date"][0]["displayDate"]
                elif "begin" in self.metadata["date"][0]:
                    record["date"] = self.metadata["date"][0]["begin"]

                elif "end" in self.metadata["date"][0]:
                    record["date"] = self.metadata["date"][0]["end"]

            elif isinstance(self.metadata["date"]["displayDate"], list):
                record["date"] = self.metadata["date"]["displayDate"][0]

            else:
                record["date"] = self.metadata["date"]["displayDate"]

        if "title" in self.metadata:
            if isinstance(self.metadata["title"], list):
                record["title"] = self.metadata["title"][0]

            else:
                record["title"] = self.metadata["title"]

        if "subject" in self.metadata:
            record["subjects"] = [subject["name"] for subject in self.metadata["subject"]]

        if "specType" in self.metadata:
            record["type"] = self.metadata["specType"]

        if "creator" in self.metadata:
            record["creator"] = self.metadata["creator"]

        if "language" in self.metadata:

            record["language"] = [lang["name"] for lang in self.metadata["language"]]

        if "type" in self.metadata:
            record["type"] = self.metadata["type"]


        self.record = record





