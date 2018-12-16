#!/usr/bin/env bash

virtualenv -p python .env

./.env/bin/pip install -r pip-dep.txt
 
