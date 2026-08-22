import sys, copy, struct
sys.path.insert(0, 'tools/font_tools')
from font_codec import *

FONT_PATHS = [
    'files/graphic/font/font_00000000.bin',
    'files/graphic/font/font_00000001.bin',
    'files/graphic/font/font_00000002.bin',
    'files/graphic/font/font_00000003.bin',
    'files/graphic/font/font_00000004.bin',
    'files/graphic/font/font_00000010.bin',
]

def load_charmap():
    codes = {}
    with open('charmap.txt', encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n')
            if '=' in line:
                left, right = line.split('=', 1)
                if len(left) == 4:
                    try:
                        codes[right] = int(left, 16)
                    except ValueError:
                        pass
    return codes

def grid_copy(g):
    return [row[:] for row in g]

def process_font(FONT_PATH, codes):
    hdr, glyphs, widths = load_font(FONT_PATH)

    def base(ch):
        return grid_copy(glyphs[codes[ch]-1]), widths[codes[ch]-1]

    # acute accent rows, extracted from proven-working accented letters
    acc_e_lower, _ = base('é')   # rows 3-5 hold the accent
    acc_E_upper, _ = base('É')   # rows 0-2 hold the accent
    ACUTE_LOWER_ROWS = acc_e_lower[3:6]
    ACUTE_UPPER_ROWS = acc_E_upper[0:3]

    new_glyphs = {}  # code -> (grid, width)

    # --- acute accent letters: c/n/s/z + C/N/S/Z ---
    for lo, up in [('c','C'), ('n','N'), ('s','S'), ('z','Z')]:
        g_lo, w_lo = base(lo)
        g_lo[3:6] = [row[:] for row in ACUTE_LOWER_ROWS]
        g_up, w_up = base(up)
        g_up[0:3] = [row[:] for row in ACUTE_UPPER_ROWS]
        new_glyphs[('acute_lo', lo)] = (g_lo, w_lo)
        new_glyphs[('acute_up', up)] = (g_up, w_up)

    # --- z with dot above (z, Z) ---
    g_z, w_z = base('z')
    for r in range(3,6):
        g_z[r] = [0]*16
    g_z[4][3] = 1; g_z[4][4] = 1
    g_z[5][3] = 1; g_z[5][4] = 1
    new_glyphs[('dot_lo','z')] = (g_z, w_z)

    g_Z, w_Z = base('Z')
    for r in range(0,3):
        g_Z[r] = [0]*16
    g_Z[0][3] = 1; g_Z[0][4] = 1
    g_Z[1][3] = 1; g_Z[1][4] = 1
    new_glyphs[('dot_up','Z')] = (g_Z, w_Z)

    # --- ogonek (a, e + A, E) ---
    def add_ogonek_lower(g):
        g[13][4] = 1; g[13][5] = 1
        g[14][5] = 1; g[14][6] = 2
        g[15][5] = 2; g[15][6] = 1
        return g
    def add_ogonek_upper(g):
        g[13][4] = 1; g[13][5] = 1
        g[14][5] = 1; g[14][6] = 2
        g[15][5] = 2; g[15][6] = 1
        return g

    g_a, w_a = base('a'); add_ogonek_lower(g_a)
    new_glyphs[('ogonek_lo','a')] = (g_a, w_a)
    g_e, w_e = base('e'); add_ogonek_lower(g_e)
    new_glyphs[('ogonek_lo','e')] = (g_e, w_e)

    g_A, w_A = base('A'); add_ogonek_upper(g_A)
    new_glyphs[('ogonek_up','A')] = (g_A, w_A)
    g_E, w_E = base('E'); add_ogonek_upper(g_E)
    new_glyphs[('ogonek_up','E')] = (g_E, w_E)

    # --- l with stroke (l, L) ---
    g_l, w_l = base('l')
    g_l[8][2] = 1
    g_l[9][1] = 1; g_l[9][2] = 1; g_l[9][3] = 1
    g_l[10][3] = 1
    new_glyphs[('stroke','l')] = (g_l, w_l)

    g_L, w_L = base('L')
    g_L[7][1] = 1
    g_L[8][0] = 1; g_L[8][1] = 1; g_L[8][2] = 1
    g_L[9][2] = 1
    new_glyphs[('stroke','L')] = (g_L, w_L)

    # map to target codes (free unmapped slots 493-508)
    assignment = [
        ('a_ogonek', ('ogonek_lo','a'), 493, 'ą'),
        ('A_ogonek', ('ogonek_up','A'), 494, 'Ą'),
        ('c_acute',  ('acute_lo','c'),  495, 'ć'),
        ('C_acute',  ('acute_up','C'),  496, 'Ć'),
        ('e_ogonek', ('ogonek_lo','e'), 497, 'ę'),
        ('E_ogonek', ('ogonek_up','E'), 498, 'Ę'),
        ('l_stroke', ('stroke','l'),    499, 'ł'),
        ('L_stroke', ('stroke','L'),    500, 'Ł'),
        ('n_acute',  ('acute_lo','n'),  501, 'ń'),
        ('N_acute',  ('acute_up','N'),  502, 'Ń'),
        ('s_acute',  ('acute_lo','s'),  503, 'ś'),
        ('S_acute',  ('acute_up','S'),  504, 'Ś'),
        ('z_acute',  ('acute_lo','z'),  505, 'ź'),
        ('Z_acute',  ('acute_up','Z'),  506, 'Ź'),
        ('z_dot',    ('dot_lo','z'),    507, 'ż'),
        ('Z_dot',    ('dot_up','Z'),    508, 'Ż'),
    ]

    with open(FONT_PATH, 'rb') as f:
        data = bytearray(f.read())

    gs = glyph_size(hdr)
    off = hdr['headerSize']
    for name, key, code, ch in assignment:
        grid, width = new_glyphs[key]
        raw = encode_glyph(grid, hdr['glyphWidth'], hdr['glyphHeight'])
        glyph_idx = code - 1
        data[off+glyph_idx*gs : off+(glyph_idx+1)*gs] = raw
        data[hdr['widthDataStart']+glyph_idx] = width

    with open(FONT_PATH, 'wb') as f:
        f.write(data)
    print(f"{FONT_PATH}: wrote {len(assignment)} glyphs")

def main():
    codes = load_charmap()
    for font_path in FONT_PATHS:
        process_font(font_path, codes)
    print("done")

if __name__ == '__main__':
    main()
