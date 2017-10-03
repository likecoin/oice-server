#!/bin/sh

# builder directory
cd /usr/local/o2Build3/
node builder3.js -e 3.0.5 $1 $2
