
##DPLA API Interactions

Code to interact with the DPLA API. Designed specifically to produce output suited to further, manual data entry, for eventual conversion to RDF according to the [Collex standard](http://wiki.collex.org/index.php/Main_Page).


    from dpla_api import DplaApi
    da = DplaApi()
    da.search("abolitionists movements", page_size=500) # Run search, page_size is capped (by DPLA) at 500, but code will iterate through as many pages as necessary to gather all results.
    da.build_arc_rdf_dataset()

    Query: abolitionists movements
    ----Accessing results page 2
    ----Accessing results page 3
    ----Accessing results page 4
    ----Accessing results page 5
    ----Accessing results page 6
    ----Accessing results page 7
    ----Accessing results page 8
    ----Accessing results page 9
    ----Accessing results page 10
    ----Accessing results page 11
    ----Accessing results page 12
    ----Accessing results page 13
    ----Accessing results page 14
    ----Accessing results page 15
    ----Accessing results page 16
    ----Accessing results page 17
    ----Accessing results page 18
    Query 'abolitionists movements' returned 8884 records (Check: 8884 records transferred)



    da.create_tsv() # create TSV results file.

A specific example of a series of searches drawing from a JSON list of terms.


    from dpla_api import DplaApi
    da = DplaApi()
    import json
    with open("data/estc_subject_list_20150312.json", "r") as estc_subjects:
        subjects = json.load(estc_subjects)
        for subject in subjects:
            da.search(subject, page_size=500)
            da.build_arc_rdf_dataset()
        print "Returned {0} total results".format(len(da.metadata_records))
    da.create_tsv()
