#!/bin/bash
rawSource=$1
jpg=$2

darktable-cli $rawSource $jpg > /dev/null 2>&1
