const { data } = require("jquery");

const INFO_ITEMS = "?s ?name ?url ?id ?partOf ?license"; /// items to select in SPARQL query

/// Create SPARQL query to get all collections data
function makeCollectionQuery() {
  return `PREFIX n4oc: <https://graph.nfdi4objects.net/collection/>
     SELECT ${INFO_ITEMS} (GROUP_CONCAT(DISTINCT ?type;separator=";") AS ?types)
     WHERE {
      ?s <http://purl.org/dc/terms/isPartOf> n4oc: .
      ?s <http://schema.org/name> ?name .
      ?s <http://xmlns.com/foaf/0.1/homepage> ?url .
      ?s <http://www.w3.org/2004/02/skos/core%23notation> ?id .
      ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns%23type> ?type .
      ?s <http://purl.org/dc/terms/isPartOf> ?partOf .
      OPTIONAL { ?s <http://purl.org/dc/terms/license> ?license . }
     }
     GROUP by ${INFO_ITEMS}`;
}

/// Create SPARQL query to count triples for a given URI
function countIndexQuery(uri) {
  return `SELECT (COUNT(?p) AS ?numTriples) WHERE {<${uri}> ?p ?o .}`;
}

/// Create SPARQL query to count triples in a collection
function countCollectionQuery(coll_uri) {
  return `SELECT (COUNT(*) as ?numTriples) {GRAPH <${coll_uri}> {?s ?p ?o}}`;
}

/// Query the Fuseki endpoint with a SPARQL query string
function query_fuseki(query_str, f) {
  var req = {
    method: 'POST',
    headers: { 'Accept': 'application/json, text/plain, */*', 'Content-Type': 'application/json' }, 
    body: JSON.stringify({ "data": query_str })
  }
  fetch(`/fuseki`, req)
    .then(response => response.json())
    .then(js => f(js))
    .catch(err => console.error(err))
    .finally(() => { console.log('fuseki fetch done'); });
}

/// Get number of triples in a collection
function getNumTriples(uri, f) {
  query_fuseki(countCollectionQuery(uri),
    response => {
      const b = JSON.parse(response).results.bindings[0];
      const numtriples = parseInt(b.numTriples.value);
      f(numtriples);
    });
}

/// Convert a SPARQL binding to a collection item
function binding2item(b) {
  let item = {
    id: parseInt(b.id.value),
    name: b.name.value,
    url: b.url.value,
    partOf: b.partOf.value,
    type: b.types.value.split(";"),
    license: b.license ? b.license.value : '',
    db: '',
    uri: b.s.value
  };
  return item;
};
