Typically, we deploy [Elasticsearch] in a single-node configuration with the security feature of
[xpack][disabling-xpack] disabled. We use Elasticsearch's Python package for data ingestion and
search operations.

In contrast to semi-structured benchmarking, unstructured datasets for Elasticsearch require no
preprocessing.

[disabling-xpack]: https://www.elastic.co/guide/en/elasticsearch/reference/current/security-settings.html
[Elasticsearch]: https://www.elastic.co/downloads/elasticsearch
