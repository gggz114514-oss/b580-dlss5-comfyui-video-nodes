"""Materialize installation paths without changing model/kernel arithmetic."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def expand(value):
    if isinstance(value, dict):
        return {expand(k): expand(v) for k, v in value.items()}
    if isinstance(value, list):
        return [expand(v) for v in value]
    if isinstance(value, str):
        return value.replace('${ROOT}', ROOT.as_posix())
    return value


def prepare():
    for cache in ('exact-cache', 'fast-cache'):
        templates = json.loads((ROOT / 'templates' / (cache + '-groups.json')).read_text())
        for relative, group in templates.items():
            target = ROOT / 'data' / cache / relative
            target.write_text(json.dumps(expand(group)), encoding='utf-8')
    profile = expand(json.loads((ROOT / 'templates/profile-v1.json').read_text()))
    profile_path = ROOT / 'data/product-v1/profile-v1.json'
    profile_path.write_text(json.dumps(profile), encoding='utf-8')
    (profile_path.parent / 'local-runtime-v1.json').write_text(json.dumps({'profile_sha256': sha(profile_path)}), encoding='utf-8')
    catalog = expand(json.loads((ROOT / 'templates/catalog.json').read_text()))
    # Original exact source bytes must remain identical after relocation.
    for path, digest in catalog['source_files'].items():
        if sha(path) != digest:
            raise RuntimeError('Exact source changed: ' + path)
    catalog_path = ROOT / 'data/exact-catalog.json'
    catalog_path.write_text(json.dumps(catalog), encoding='utf-8')
    package = expand(json.loads((ROOT / 'templates/package.json').read_text()))
    package['catalog'] = str(catalog_path)
    package['catalog_sha256'] = sha(catalog_path)
    package['cache'] = str(ROOT / 'data/exact-cache')
    (ROOT / 'data/exact-package.json').write_text(json.dumps(package), encoding='utf-8')
    (ROOT / 'run-locks').mkdir(exist_ok=True)
    (ROOT / 'data/installed-at.txt').write_text(ROOT.as_posix(), encoding='utf-8')


if __name__ == '__main__':
    prepare()
    print('NR paths prepared: ' + str(ROOT))
