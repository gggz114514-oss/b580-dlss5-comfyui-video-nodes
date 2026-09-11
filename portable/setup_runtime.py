"""Prepare pinned model resources and relocatable cache paths; never load the DLL."""
import argparse
import hashlib
import io
from pathlib import Path
import struct
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parent
MODEL_URL = 'https://github.com/RankFTW/rhi-repo/releases/download/dlssnr-310.8.SF-v2/nvngx_dlssnr_310.8.SF-v2.zip'
ZIP_SHA = '1da35941894994eb087e017577829e492454e9bae3a6a9397027069ceb74955c'
DLL_SHA = '6eb209e764f39872625debd6abaf45e2bb6322f6f270f781f70c059ae30b3927'
WEIGHTS_SHA = '836f445d06ecd2e59bb9f17b84b91c143396fd76ccda1c9dc7fe81d5edd548f4'


def extract_weights(data):
    if hashlib.sha256(data).hexdigest() != DLL_SHA:
        raise ValueError('NR DLL version/checksum mismatch')
    u16 = lambda offset: struct.unpack_from('<H', data, offset)[0]
    u32 = lambda offset: struct.unpack_from('<I', data, offset)[0]
    nt = u32(0x3c)
    optional = nt + 24
    section_start = optional + u16(nt + 20)
    sections = []
    for index in range(u16(nt + 6)):
        entry = section_start + index * 40
        sections.append((u32(entry + 12), u32(entry + 16), u32(entry + 20)))

    def offset(rva):
        for address, size, raw in sections:
            if address <= rva < address + size:
                return raw + rva - address
        raise ValueError('Resource RVA outside PE sections')

    resource = offset(u32(optional + (112 if u16(optional) == 0x20b else 96) + 16))

    def entries(relative):
        directory = resource + relative
        for index in range(u16(directory + 12) + u16(directory + 14)):
            entry = directory + 16 + index * 8
            name, child = u32(entry), u32(entry + 4)
            if name & 0x80000000:
                address = resource + (name & 0x7fffffff)
                name = data[address + 2:address + 2 + 2 * u16(address)].decode('utf-16-le')
            yield name, child

    for _, type_child in entries(0):
        if not type_child & 0x80000000:
            continue
        for name, name_child in entries(type_child & 0x7fffffff):
            if name != 'WEIGHTS_HT':
                continue
            languages = list(entries(name_child & 0x7fffffff))
            if len(languages) != 1:
                raise ValueError('Unexpected resource languages')
            entry = resource + languages[0][1]
            start, size = offset(u32(entry)), u32(entry + 4)
            weights = data[start:start + size]
            if hashlib.sha256(weights).hexdigest() != WEIGHTS_SHA:
                raise ValueError('Extracted weights checksum mismatch')
            return weights
    raise ValueError('WEIGHTS_HT resource absent')


def setup(dll=None):
    target = ROOT / 'exact/model-assets/sf-v2/WEIGHTS_HT.bin'
    if not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest() != WEIGHTS_SHA:
        if dll:
            data = Path(dll).read_bytes()
        else:
            print('Downloading pinned SF-v2 model resource from upstream GitHub...', flush=True)
            with urllib.request.urlopen(MODEL_URL, timeout=90) as response:
                archive = response.read()
            if hashlib.sha256(archive).hexdigest() != ZIP_SHA:
                raise ValueError('Model archive checksum mismatch')
            with zipfile.ZipFile(io.BytesIO(archive)) as zipped:
                candidates = [name for name in zipped.namelist() if name.lower().endswith('.dll')]
                data = next((value for name in candidates if hashlib.sha256(value := zipped.read(name)).hexdigest() == DLL_SHA), None)
            if data is None:
                raise ValueError('Pinned DLL absent from model archive')
        weights = extract_weights(data)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(weights)
    from relocate import prepare
    prepare()
    print('Model and runtime prepared.', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dll', type=Path, help='Optional already-downloaded pinned SF-v2 DLL')
    options = parser.parse_args()
    setup(options.dll)
