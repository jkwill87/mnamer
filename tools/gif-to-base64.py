import base64
import sys

# Will output the base64 representation of a an image
if not sys.argv[1]:
    print("Usage: _b64.py img.gif")
    sys.exit(1)
with open(sys.argv[1], 'rb') as gif_file:
    data = gif_file.read()
    print(base64.encodestring(data).decode('utf8'))
