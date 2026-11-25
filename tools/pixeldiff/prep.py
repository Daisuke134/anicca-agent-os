from PIL import Image
import sys
src, dst = sys.argv[1], sys.argv[2]
im = Image.open(src).convert('RGB')
im = im.resize((540, 960))
im.save(dst)
