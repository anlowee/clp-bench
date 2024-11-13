The version of MongoDB we benchmarked is `6.0.19`. We use `mongosh`, `mongod`, `mongoexport`, and 
`mongoimport` to ingest the dataset and perform query benchmarking. No special preprocessing is 
required for the dataset. Specifically, we use the [ZStandard][zstandard] compressor with the 
[default compression level][compression_level] set to 3.

[compression_level]: https://source.wiredtiger.com/3.1.0/compression.html#:~:text=%22extensions%3D%5B%2Fusr%2Flocal%2Flib%2Flibwiredtiger_zstd.sothe%20additional%20configuration%20argument%20compression_level%20.
[zstandard]: https://www.mongodb.com/docs/manual/reference/program/mongod/#std-option-mongod.--wiredTigerCollectionBlockCompressor
