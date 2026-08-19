# n4o-graph-admin / grimpo-admin

Web service for administration of a knowledge graph managed with [grimpo].

This application adds a user interface on top of the actual knowledge graph importer.

Development is being funded as part of [NFDI4Objects](https://www.nfdi4objects.net/) to build the [NFDI4Objects Knowledge Graph](https://graph.nfdi4objects.net/). 

## Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [License](#license)

## Installation

Requires Python. You can call `make deps` to install dependencies into a local `.venv` directory and to install required JavaScript libraries.

## Configuration

- `GRIMPO` - [grimpo](https://github.com/nfdi4objects/grimpo) API base URL. Default: <http://importer:5020>
- `SPARQL` - SPARQL Query endpoint. Default: <http://fuseki:3030/n4o>

The service is started at <http://localhost:5010> by default.

Example:

~~~sh
GRIMPO=http://localhost:5020 SPARQL=http://localhost:5020/sparql python app.py
~~~~

## License

Licensed under [Apache License](http://www.apache.org/licenses/) 2.0.


[grimpo]: https://github.com/nfdi4objects/grimpo
