
# coding: utf-8


import lxml
from lxml import etree
import subprocess
import sys
from filecmp import cmp
import io
import os.path
import sys, getopt




ns = {'owl': 'http://www.w3.org/2002/07/owl#', 'rdf':'http://www.w3.org/1999/02/22-rdf-syntax-ns#', 'rdfs':'http://www.w3.org/2000/01/rdf-schema#'}


def main(argv):
    
    orig_file = 'pizza_consistent_rdf.owl'
    tmp_file = "tmp.owl"
    
    
    try:
        opts, args = getopt.getopt(argv,"hi:o:",["input=", "output="])

    except getopt.GetoptError:
        print ('script.py -i <input> -o <output>')
        sys.exit(2)
    
    for opt, arg in opts:
        if opt == '-h':
            print ('script.py -i <input> -o <output>')
            sys.exit()
        elif opt in ("-o", "--output"):
            reduced_file = arg
        elif opt in ("-i", "--input"):
            orig_file = arg            
    
    tree = etree.parse(orig_file)
    

    #get the root of the XML tree
    root = tree.getroot()


    #retrieve the list of subClassOf elements with XPath
    clauses = root.xpath('/rdf:RDF/owl:Class/rdfs:subClassOf', namespaces=ns)

    print('There are ' + str(len(clauses)) + ' clauses in the ontology')



    #wrapper for Hermit reasoner to check if the ontology in the first file entails the one in the second
    def check(f1, f2):
        test = subprocess.Popen(
            ["java", "-jar", "HermiT.jar",
             "--premise=file://" + os.path.abspath(f1),
             "--conclusion=file://" + os.path.abspath(f2),
             "-E"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        out, err = test.communicate()
        return out.decode() == 'true\n'


    #list of redundant clauses
    redundants = []

    #iterate through the clauses
    for i, clause in enumerate(clauses):
        
        
        if i% int(len(clauses)/40) == 0:
            print(str(i/len(clauses)))
            print(len(redundants))
        
        #retrieve the parent of the subClassOf element, i.e. the subclass in the clause    
        parent = clause.getparent()
        
        #try to remove the current clause
        parent.remove(clause)
        
        #write the resulting XML tree (representing the reduced ontology) to file
        tree.write(tmp_file, pretty_print=True)
        
        #check if the entailment holds in both directions
        if check(tmp_file, orig_file) and check(orig_file, tmp_file):
            #if it holds then the clause is redundant
            print('redundant clause!!!')
            
            #retrive the name of the subclass
            p = parent.xpath('@rdf:about',namespaces=ns)[0]
            
            #retrive the superclass (it can be both a proper class or an anonymous one)
            restrictions = clause.xpath('owl:Restriction', namespaces=ns)
            resources = clause.xpath('@rdf:resource', namespaces=ns)

            #if the superclass is an anonymous one
            if len(restrictions) > 0:
                redundants.append((p, restrictions[0], True))
            
            #if the superclass is a proper class    
            if len(resources) > 0:
                redundants.append((p, resources[0], False))
            
        else:
            #otherwise, add again the non-redundant clause
            parent.append(clause)
        
    #try to delete the temporary file used to check the redundancies
    try:
        os.remove(tmp_file)
    except OSError:
        pass
    
    #write the final reduced ontology to file
    tree.write(reduced_file, pretty_print=True)
    
    #print the redundant clauses found
    for i in range(len(redundants)):
        print(i)
        print('Subclass: ' + redundants[i][0])
        
        if (redundants[i][2]):
            print('Superclass: ')
            etree.dump(redundants[i][1], pretty_print=True)
        else:
            print('Superclass: ' + redundants[i][1])

        print('\n\n')


if __name__ == "__main__":
   main(sys.argv[1:])
