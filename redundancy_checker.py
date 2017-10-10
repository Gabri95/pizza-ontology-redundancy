
# coding: utf-8


import lxml
from lxml import etree
import subprocess
import sys
from filecmp import cmp
import io


ns = {'owl': 'http://www.w3.org/2002/07/owl#', 'rdf':'http://www.w3.org/1999/02/22-rdf-syntax-ns#', 'rdfs':'http://www.w3.org/2000/01/rdf-schema#'}


orig_file = 'pizza_consistent_rdf.owl'


#/home/davide/Jupyter Notebook Projects/DL/
tree = etree.parse(orig_file)


xslt=b'''<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml" indent="no"/>

<xsl:template match="/|comment()|processing-instruction()">
    <xsl:copy>
      <xsl:apply-templates/>
    </xsl:copy>
</xsl:template>

<xsl:template match="*">
    <xsl:element name="{local-name()}">
      <xsl:apply-templates select="@*|node()"/>
    </xsl:element>
</xsl:template>

<xsl:template match="@*">
    <xsl:attribute name="{local-name()}">
      <xsl:value-of select="."/>
    </xsl:attribute>
</xsl:template>
</xsl:stylesheet>
'''
IO = io.BytesIO(xslt)
xslt_doc=etree.parse(IO)
transform=etree.XSLT(xslt_doc)

#get the root of the XML tree
root = tree.getroot()

#retrieve the list of subClassOf elements with XPath
clauses = root.xpath('/rdf:RDF/owl:Class/rdfs:subClassOf', namespaces=ns)

print('There are ' + str(len(clauses)) + ' clauses in the ontology')



#wrapper for Hermit reasoner to check if the ontology in the first file entails the one in the second
def check(f1, f2):
    test = subprocess.Popen(
        ["java", "-jar", "HermiT.jar",
         "--premise=file:///home/gabriele/Documents/KR/Assignment_2/" + f1,
         "--conclusion=file:///home/gabriele/Documents/KR/Assignment_2/" + f2,
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
    tree.write('reduced_pizza.owl', pretty_print=True)
    
    #check if the entailment holds in both directions
    if check('reduced_pizza.owl', orig_file) and check(orig_file, 'reduced_pizza.owl'):
        #if it holds then the clause is redundant
        print('redundant clause!!!')
        
        #retrive the name of the subclass
        p = parent.xpath('@rdf:about',namespaces=ns)
        
        #retrive the superclass (it can be both a proper class or an anonymous one)
        restrictions = clause.xpath('owl:Restriction', namespaces=ns)
        resources = clause.xpath('@rdf:resource', namespaces=ns)

        #if the superclass is an anonymous one
        if len(restrictions) > 0:
            r = transform(etree.ElementTree(restrictions[0]))
            redundants.append((p, r, True))
        
        #if the superclass is a proper class    
        if len(resources) > 0:
            redundants.append((p, resources[0], False))
        
    else:
        #otherwise, add again the non-redundant clause
        parent.append(clause)
    

#print the redundant clauses found
for i in range(len(redundants)):
    print(i)
    print(redundants[i][0])
    if (redundants[i][2]):
        redundants[i][1].write(sys.stdout, pretty_print=True)
    else:
        print(redundants[i][1])

