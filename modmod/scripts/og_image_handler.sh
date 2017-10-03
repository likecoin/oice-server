#!/bin/sh
cd $1

convert $3 -resize 1200x630 -gravity center -background black -extent 1200x630 og_image.jpg
convert og_image.jpg -resize 120x63 og_image_120x63.jpg
convert og_image.jpg -resize 600x315 og_image_600x315.jpg

composite -gravity center $2 og_image.jpg og_image_button.jpg
# composite -gravity center $2 og_image_thumbnail.jpg og_image_button.jpg
