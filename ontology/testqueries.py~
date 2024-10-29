filename = "demo.ttl" 
import rdflib
g = rdflib.Graph()

result = g.parse(filename, format='ttl')
print(result)
query = """
SELECT * WHERE {
        ?s ?p ?o .
}
"""

g.query(query)
for stmt in g:
    print(stmt)
