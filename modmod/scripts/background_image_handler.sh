#!/bin/sh
cd "$1"

convert "$2" -resize 1080x1080 "$2"
