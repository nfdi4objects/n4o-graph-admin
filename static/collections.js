/// Ensure collection has mandatory fields
function fixCollection(collection) {
    let coll = collection
    if (!('type' in coll)) { coll.type = []; }
    return coll;
};

/// Returns an URL for collections
function collection_url(s="") {
    return `/importer/collection/${s}`;
}

/// Get list of collections from the KG
function getCollections() {
    const req = { method: 'GET', headers:  { 'Accept': 'application/json, text/plain, */*', 'Content-Type': 'application/json' }};
    fetch(collection_url(), req)
        .then(response => response.json())
        .then(js => {
            app.collections = js.map(d => fixCollection(d));
            app.collections.sort((a, b) => a.id - b.id);
        })
        .catch(err => console.error(err))
        .finally(() => { console.log('fetch collections done'); });
}

function makeCollection(id_str, collection_tpl) {
    const collection = collection_tpl ? { ...collection_tpl } : {
        type: [],
    };
    if (collection_tpl) {
        collection.id = id_str;
        collection.name = `New Collection ${id_str}`;
        collection.uri = `https://graph.nfdi4objects.net/collection/${id_str}`;
    }
    for (let key in collection) { // remove empty fields
        if (collection[key] === '') {
            delete collection[key]
        }
    }
    return collection
}

function showProgess(on = false) {
    document.getElementById("SP1").style.display = on ? "inline-block" : "none";
}

/// Import TTL data into the KG
function postCollectionData(index,file,add_mode=false) {
    showProgess(true);
    var data = new FormData();
    data.append('file', file, file.filename);
    data.append('index', index);
    data.append('add_mode', add_mode);
    
    var req = { method: 'POST', body: data, };
    fetch('/postCollectionData/'+index, req)
        .then(response => response.json())
        .then(json => {
            console.log(json);
            if (json.code) {
                alert(`Error ${json.code}:\n\t${json.message} at line ${json.position.linecol}`);
            }
        })
        .catch(err => alert(err))
        .finally(() => {
            showProgess(false);
        });
}

function makeAppData() {
    return {
        data() {
            return {
                collections: [],
                displayCollection: null,
                collectionInfo: 'No info.',
                rdfFiles: [],
                add_mode: false,
            }
        },
        delimiters: ["${", "}$"], // for global
        compilerOptions: { delimiters: ["${", "}$"] }, // for standalone
        methods: {
            selectCollection(c_id) {
                this.displayCollection = this.collections.find(c => c.id === c_id);
            },

            delCollection() {
                /// Remove a type from the collection
                let N = this.displayCollection ? this.displayCollection.id :this.collections.length
                let id = prompt('Enter the index of the collection to delete:', N);
                id = parseInt(id) - 1;
                if (!isNaN(id) && id >= 0 || id < N) {
                    let q = this.collections[id];
                    //console.log(q.id)
                    fetch(collection_url(q.id), {
                        method: 'DELETE',
                        headers: { "Content-Type": "application/json", }
                    })
                        .then(response => response.json())
                        .then(data => {
                            console.log(data);
                            this.collections.splice(id, 1)
                            this.displayCollection = null
                        })
                        .catch(err => alert(err))
                        .finally(() => { console.log(`collection ${id} deleted`); });
                }

            },

            addCollection() {
                /// Add a new collection
                let new_id = 1;
                let N = this.collections.length;
                if (N > 0) {
                    new_id = Math.max(...this.collections.map(c => c.id)) + 1;
                }
                let lastCollection = N > 0 ? this.collections[N - 1] : null;
                const new_collection = makeCollection(new_id.toString(), lastCollection)

                fetch(collection_url(), {
                    method: 'POST',
                    headers: { "Content-Type": "application/json", },
                    body: JSON.stringify(new_collection)
                })
                    .then(response => response.json())
                    .then(data => {
                        //console.log(data);
                        this.collections.push(fixCollection(data));
                        this.selectCollection(new_id.toString());
                    })
                    .catch(err => alert(err))
                    .finally(() => { console.log('collection added'); });
            },
            showDetails(uri) {
                /// Show number of triples in collection
                getNumTriples(uri, num => {
                    this.collectionInfo = `The collection <${uri}> contains ${num} triples.`;
                    $('#collectionInfoMDialog').modal('show');
                });
            },
            deleteCollData(id) {
                if (this.displayCollection == null) {
                    alert('No collection selected for data deletion.');
                    return;
                }
                if (!confirm(`Are you sure you want to delete all data for collection ${id}? This action cannot be undone.`)) {
                    return;
                }
                showProgess(true);
                var req = { method: 'POST', headers: { 'Accept': 'application/json, text/plain, */*' } }
                fetch(collection_url(`${id}/remove`), req)
                    .then(response => response.json())
                    .then(json => console.log(json))
                    .catch(err => console.error(err))
                    .finally(() => {
                        showProgess(false);
                        alert('Data deletion completed.');
                    });
            },
            saveRDFUrl(event) {
                // Saves x3ml event data
                this.rdfFiles = event.target.files;
            },
            uploadRDF() {
                /// Upload RDF data from selected file
                if (this.rdfFiles.length ==0) {
                    alert('No RDF file selected for upload.');
                }
                else {
                    const file0 = this.rdfFiles[0]
                    postCollectionData(this.displayCollection.id, file0, this.add_mode);
                    this.rdfFiles = [];
                }
            },
            putCollection(collection) {
                /// Update collection metadata
                if (collection == null) {
                    alert('No collection selected for update.');
                    return;
                }
                const headers = { "Content-Type": "application/json", }
                fetch(collection_url(collection.id), {
                    method: 'PUT',
                    headers: headers,
                    body: JSON.stringify(collection)
                })
                    .then(response => response.json())
                    .then(data => { console.log(data); })
                    .catch(err => alert(err))
                    .finally(() => {
                        this.getCollection(collection.id);
                        alert('collection changed');
                    });
            },
            getCollection(id) {
                /// Retrieve collection metadata
                if (!id) {
                    alert('No collection selected for retrieval.');
                    return;
                }
                const headers = { "Accept": "application/json, text/plain, */*", }
                fetch(collection_url(id), { method: 'GET', headers: headers })
                    .then(response => response.json())
                    .then(data => { this.displayCollection = fixCollection(data); })
                    .catch(err => alert(err))
                    .finally(() => { console.log('collection fetched'); });
            },
            addType() {
                /// Add a new type to the collection
                if (this.displayCollection == null) {
                    alert('No collection selected for adding type.');
                    return;
                }
                this.displayCollection.type.push('x:y');
            },
            delType() {
                /// Remove a type from the collection
                if (this.displayCollection == null) {
                    alert('No collection selected for deleting type.');
                    return;
                }
                let N = this.displayCollection.type.length
                let id = prompt('Enter the index of the type to delete:', N);
                id = parseInt(id) - 1;
                if (!isNaN(id) && id >= 0 || id < N) {
                    this.displayCollection.type.splice(id, 1);
                }
            },
        },
        mounted() {
            document.onreadystatechange = () => {
                if (document.readyState == "complete") {
                    getCollections();
                }
            }
        },
        created() {
            console.log('created');
        }
    }
}
