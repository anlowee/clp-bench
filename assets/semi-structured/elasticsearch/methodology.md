Typically, we deploy [Elasticsearch] in a single-node configuration with the security feature of 
[xpack][disabling-xpack] disabled. We use Elasticsearch's Python package for data ingestion and 
search operations.

Some preprocessing is necessary to make the dataset searchable in Elasticsearch. For more details, 
refer to the `traverse_data` function in `ingest_script` . This process generally involves 
reorganizing specific fields, moving them into outer or inner objects to ensure proper query 
functionality.

[Elasticsearch]: https://www.elastic.co/downloads/elasticsearch  
[disabling-xpack]: https://www.elastic.co/guide/en/elasticsearch/reference/current/security-settings.html
