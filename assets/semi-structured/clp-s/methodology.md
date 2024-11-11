First, download the latest released binary, or clone the latest [code][CLP] and compile it locally
by following these [instructions][core-build]. Then we use `clp-s` binary.

The setup for CLP-S is almost the same as that of CLP. The only difference is the query format: JSON
log queries use [KQL], as specified in the `queries` field of `config.yaml` .

[CLP]: https://github.com/y-scope/clp
[core-build]: https://docs.yscope.com/clp/main/dev-guide/components-core/index.html
[KQL]: https://docs.yscope.com/clp/main/user-guide/reference-json-search-syntax.html
