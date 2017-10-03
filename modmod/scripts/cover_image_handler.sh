#!/bin/sh
cd "$1"

convert "$3" -resize 200x200 -gravity center -background black -extent 200x200 cover_image.jpg

composite -gravity center "$2" cover_image.jpg cover_image_button.jpg

convert "$3" -resize 540x540 -gravity center -background black -extent 540x540 "$3"
