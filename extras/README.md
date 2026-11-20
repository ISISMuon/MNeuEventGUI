# Extras
This folder contains extra material which is relevant to the package but not part of it.

## SVG graphics
To convert the SVG icon to an `.ico` format with ImageMagick, run the following:
```bash
magick -density 300 -define icon:auto-resize=256,128,96,64,48,32,16 -background none icon.svg icon.ico
```

To convert it to the macOS `.icns` format, render a 1024x1024 PNG with
Inkscape and convert it with Pillow:
```bash
inkscape icon.svg --export-type=png --export-filename=icon.png -w 1024 -h 1024
python -c "from PIL import Image; Image.open('icon.png').save('icon.icns')"
```

The window icon used by the app at runtime is a 256x256 PNG in the package:
```bash
inkscape icon.svg --export-type=png --export-filename=../src/MNeuEventGUI/assets/icon.png -w 256 -h 256
```
