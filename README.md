## DPLA API Interactions

Code to interact with the DPLA API. Designed specifically to produce output suited to further, manual data entry, for eventual conversion to RDF according to the [Collex standard](http://wiki.collex.org/index.php/Main_Page).

Code below can be used to connect to the DPLA API and process search results. In order to search, you'll need a DPLA [API-Key](http://dp.la/info/developers/codex/policies/#get-a-key). This should be stored in the `default.cfg`, which you'll need to update in order for the scripts below to work.

    from dpla_api import DplaApi
    da = DplaApi()
    da.search("abolitionists movements", page_size=500) # Run search, page_size is capped (by DPLA) at 500, but code will iterate through as many pages as necessary to gather all results.
    da.build_arc_rdf_dataset()


Output:

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

After results have been gathered, store the results in a tab-separated table.

    da.create_tsv() # create TSV results file.

The idea of this sequence of events is that the tsv file makes it possible to then manually edit the returned entries, particuarly when loaded into Excel or a Google spreadsheet. This workflow `DPLA->TSV->RDF` was designed specifically to support the parameters and values of ARC.

Once editing has been completed, or even if it has not -- the script will work anyway to fill in default values -- run the lines of code below to create an RDF XML file for each record, named according to its unique DPLA ID.

    from buildrdf import BuildRdf
    br = BuildRdf()
    br.build_rdf_from_tsv("data/radicalism-all-dpla.txt", lines_to_process = 1)

The `lines-to-process` parameter tells the script how many records to process, and how many files to write. 

Output of the above code, including full RDF record:

    Processing http://dp.la/api/items/0daa0bab0c6c1b95c474af2de2ca0f6c : The abolitionists; a collection of their writing
    
    <rdf:RDF xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#" 
             xmlns:collex="http://www.collex.org/schema#"         
             xmlns:dc="http://purl.org/dc/elements/1.1/" 
             xmlns:sro="http://www.lib.msu.edu/sro/schema#" 
             xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"     
             xmlns:role="http://www.loc.gov/loc.terms/relators/" 
             xmlns:dcterms="http://purl.org/dc/terms/">
        <sro:dpla rdf:about="http://dp.la/api/items/0daa0bab0c6c1b95c474af2de2ca0f6c">
            <collex:federation>SRO</collex:federation>
            <collex:archive>DPLA</collex:archive>
            <dc:title>The abolitionists; a collection of their writing</dc:title>
            <role:CRE>Ruchames, Louis, 1917-</role:CRE>
            <dc:source>HathiTrust</dc:source>
            <dc:subject>Antislavery movements--United States</dc:subject>
            <dc:subject>Slavery--United States--Controversial literature</dc:subject>
            <dc:subject>Abolitionists</dc:subject>
            <collex:discipline>History</collex:discipline>
            <collex:genre>Nonfiction</collex:genre>
            <dc:type>Codex</dc:type>
            <dc:date>
                <rdfs:label>[1963]</rdfs:label>
                <rdf:value>1963</rdf:value>
            </dc:date>
            <collex:fulltext>TRUE</collex:fulltext>
            <dc:language>English</dc:language>
            <rdfs:seeAlso rdf:resource="http://catalog.hathitrust.org/Record/000408823"/>
            <collex:thumbnail rdf:resource="https://books.google.com/books/content?id=9Ml2AAAAMAAJ&amp;printsec=frontcover&amp;img=1&amp;zoom=5"/>
        </sro:dpla>
    </rdf:RDF>


---


Code below used to load a list of thousands of searches and run them all in sequence, before storing the results in a tsv file.

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