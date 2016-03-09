"""Access HathiTrust bibliographic API: https://www.hathitrust.org/bib_api."""
import requests


class HathiBibApi(object):
    """Access metadata via the HathiTrust bibliographic API."""

    def __init__(self):
        """Init urls."""
        self.base_url_brief = "http://catalog.hathitrust.org/api/volumes/brief/<idtype>/<idvalue>.json"
        self.base_url_full = "http://catalog.hathitrust.org/api/volumes/full/<idtype>/<idvalue>.json"

    def get_record(self, id_value, result_type="full", id_type="recordnumber"):
        """Return record via call to API.

        args:
            id_value(str): the id value to be included in the request url.
        kwargs:
            result_type(str): either 'full' or 'brief', specifying the type of
                result to get back (full results include complete MARC record)
            id_type(str): HT allows a variety of id types to be used.
        """
        if result_type == "full":
            self.request_url = self.base_url_full.replace("<idtype>", id_type)\
                                                 .replace("<idvalue>", id_value)
        elif result_type == "brief":
            self.request_url = self.base_url_brief.replace("<idtype>", id_type)\
                                                 .replace("<idvalue>", id_value)
        else:
            raise ValueError("Invalid result_type: {0}".format(result_type))

        return self._make_request()

    def _make_request(self):
        """Make request with self.request_url."""
        # print self.request_url
        return requests.get(self.request_url).json()
