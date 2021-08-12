#!/bin/bash
pushd $(dirname "$0")
generate_api shield.json
sgqlc-codegen schema --docstrings shield.json
rm -f shield.json
popd
