# Extras
This folder contains extra material which is relevant to the package but not part of it.

## SVG graphics
To convert the SVG icon to an `.ico` format with ImageMagick, run the following:
```bash
magick -density 300 -define icon:auto-resize=256,128,96,64,48,32,16 -background none icon.svg icon.ico
```
