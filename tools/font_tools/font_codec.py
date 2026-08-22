"""Codec for pokeheartgold's custom 2bpp font glyph format (font_data.c)."""
import struct

HEADER_FMT = '<IIIBBBB'
HEADER_SIZE = struct.calcsize(HEADER_FMT)

def parse_header(data):
    headerSize, widthDataStart, numGlyphs, fixedWidth, fixedHeight, glyphWidth, glyphHeight = struct.unpack_from(HEADER_FMT, data, 0)
    return dict(headerSize=headerSize, widthDataStart=widthDataStart, numGlyphs=numGlyphs,
                fixedWidth=fixedWidth, fixedHeight=fixedHeight, glyphWidth=glyphWidth, glyphHeight=glyphHeight)

def glyph_size(hdr):
    return 16 * hdr['glyphWidth'] * hdr['glyphHeight']

def decode_subtile_8x8(raw16bytes):
    """Decode one 8x8 sub-tile (16 raw bytes, 2bpp) into an 8x8 grid of values 0-3.
    Verified against GLYPH_COPY_4BPP/DecompressGlyphTile: for row bytes (b0,b1) at
    offsets (2*row, 2*row+1), columns 0-3 come from b1, columns 4-7 come from b0."""
    px = [[0]*8 for _ in range(8)]
    for row in range(8):
        b0 = raw16bytes[row*2]
        b1 = raw16bytes[row*2+1]
        vals = [
            (b1 >> 6) & 3, (b1 >> 4) & 3, (b1 >> 2) & 3, b1 & 3,
            (b0 >> 6) & 3, (b0 >> 4) & 3, (b0 >> 2) & 3, b0 & 3,
        ]
        px[row] = vals
    return px

def encode_subtile_8x8(px):
    """Encode an 8x8 grid of values 0-3 into 16 raw bytes (2bpp)."""
    raw = bytearray(16)
    for row in range(8):
        vals = px[row]
        b1 = (vals[0]<<6)|(vals[1]<<4)|(vals[2]<<2)|vals[3]
        b0 = (vals[4]<<6)|(vals[5]<<4)|(vals[6]<<2)|vals[7]
        raw[row*2] = b0
        raw[row*2+1] = b1
    return bytes(raw)

def decode_glyph(raw64bytes, glyphWidth, glyphHeight):
    """Decode a full glyph (glyphWidth*8 x glyphHeight*8 px) from its raw sub-tile bytes.
    Sub-tile order in source matches DecompressGlyphTiles_FromPreloaded offsets:
      8x8:   [0]
      8x16:  [0]=top, [0x10]=bottom
      16x8:  [0]=left, [0x10]=right
      16x16: [0]=top-left, [0x10]=top-right, [0x20]=bottom-left, [0x30]=bottom-right
    """
    w, h = glyphWidth, glyphHeight
    W, H = w*8, h*8
    grid = [[0]*W for _ in range(H)]
    subtiles = [raw64bytes[i*16:(i+1)*16] for i in range(w*h)]
    # NDS tile layout order for the given src offsets: sequential tiles in offset order 0,0x10,0x20,0x30
    # For 16x16 (w=2,h=2): offsets 0,0x10,0x20,0x30 = top-left, top-right, bottom-left, bottom-right
    idx = 0
    for ty in range(h):
        for tx in range(w):
            sub = decode_subtile_8x8(subtiles[idx])
            for r in range(8):
                for c in range(8):
                    grid[ty*8+r][tx*8+c] = sub[r][c]
            idx += 1
    return grid

def encode_glyph(grid, glyphWidth, glyphHeight):
    w, h = glyphWidth, glyphHeight
    raw = bytearray(16*w*h)
    idx = 0
    for ty in range(h):
        for tx in range(w):
            sub = [[grid[ty*8+r][tx*8+c] for c in range(8)] for r in range(8)]
            raw[idx*16:(idx+1)*16] = encode_subtile_8x8(sub)
            idx += 1
    return bytes(raw)

def load_font(path):
    with open(path, 'rb') as f:
        data = f.read()
    hdr = parse_header(data)
    gs = glyph_size(hdr)
    glyphs = []
    off = hdr['headerSize']
    for i in range(hdr['numGlyphs']):
        raw = data[off+i*gs: off+(i+1)*gs]
        glyphs.append(decode_glyph(raw, hdr['glyphWidth'], hdr['glyphHeight']))
    widths = list(data[hdr['widthDataStart']: hdr['widthDataStart']+hdr['numGlyphs']])
    return hdr, glyphs, widths
