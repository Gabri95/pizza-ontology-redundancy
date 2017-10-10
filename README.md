# pizza-ontology-redundancy

Second project for the Knowledge Representation course in the MSc Artificial Intelligence at the University of Amsterdam.

We wrote a Python script which go through the RDF/XML file representing an ontology and try to remove the redundant clasues, employing the HermiT reasoner.

Usage:

python redundancy_checker.py -i <original_ontology> -o <output_file>

where "original_ontology" should be the RDF/XML file containing the original ontology (the file 'pizza_consistent_rdf.owl') while "output_file" will contain the resulting reduced ontology.
