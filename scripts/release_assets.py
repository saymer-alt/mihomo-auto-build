# SPDX-License-Identifier: MIT
"""MIPSel publication state machine. Never overwrite a healthy binary."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys


class MetadataError(Exception):
    pass


class NotFound(Exception):
    pass


class GitHub:
    def api(self, path, method='GET', fields=None, raw=False):
        args = ['gh', 'api', path, '-X', method]
        if raw:
            args += ['-H', 'Accept: application/octet-stream']
        for key, value in (fields or {}).items():
            args += ['-f', f'{key}={value}']
        result = subprocess.run(args, capture_output=True)
        if result.returncode:
            if method == 'GET' and re.search(rb'\(HTTP 404\)', result.stderr):
                raise NotFound(path)
            raise MetadataError('GitHub API failed; no repair authorized')
        if raw:
            return result.stdout
        if method == 'DELETE':
            return None
        try:
            return json.loads(result.stdout)
        except (ValueError, UnicodeError) as error:
            raise MetadataError('Invalid GitHub JSON') from error

    def upload(self, tag, path):
        # No --clobber: an unexpected concurrent asset causes a safe failure.
        subprocess.run(['gh', 'release', 'upload', tag, str(path)], check=True)


def digest(asset):
    value = asset.get('digest')
    if not isinstance(value, str) or not re.fullmatch(r'sha256:[0-9a-f]{64}', value):
        raise MetadataError('Missing/invalid GitHub SHA-256 digest')
    return value[7:]


def starter(asset):
    return (asset.get('state') == 'starter' and type(asset.get('size')) is int
            and asset['size'] == 0 and asset.get('digest') is None)


def read_release(api, repo, tag):
    release = api.api(f'repos/{repo}/releases/tags/{tag}')
    if (not isinstance(release, dict) or release.get('tag_name') != tag
            or release.get('draft') is not False
            or type(release.get('id')) is not int or release['id'] <= 0
            or not isinstance(release.get('assets'), list)):
        raise MetadataError('Invalid release identity/metadata')
    if any(not isinstance(a, dict) or not isinstance(a.get('name'), str) for a in release['assets']):
        raise MetadataError('Invalid asset metadata')
    return release


def inspect(api, repo, tag, binary):
    try:
        release = read_release(api, repo, tag)
    except NotFound:
        return {'mode': 'build', 'release': None, 'binary': None, 'sidecar': None}
    assets = release['assets']

    def one(name):
        found = [a for a in assets if a['name'] == name]
        if len(found) > 1:
            raise MetadataError('Duplicate expected assets')
        if not found:
            return None
        a = found[0]
        if (type(a.get('id')) is not int or a['id'] <= 0 or type(a.get('size')) is not int
                or sum(x.get('id') == a['id'] for x in assets) != 1
                or a['size'] < 0 or not (a.get('state') == 'uploaded' or starter(a))):
            raise MetadataError('Invalid asset identity/size/state')
        return a

    b, s = one(binary), one(binary + '.sha256')
    state = {'release': release['id'], 'binary': b, 'sidecar': s}
    if not b or b['size'] == 0:
        return dict(state, mode='build')
    expected = digest(b)
    if not s or s['size'] == 0:
        return dict(state, mode='checksum')
    if s['size'] > 4096:
        raise MetadataError('Oversized checksum sidecar')
    content = api.api(f'repos/{repo}/releases/assets/{s["id"]}', raw=True)
    if len(content) != s['size'] or hashlib.sha256(content).hexdigest() != digest(s):
        raise MetadataError('Sidecar bytes disagree with GitHub metadata')
    if content != f'{expected}  {binary}\n'.encode():
        raise MetadataError('Checksum does not match the published binary')
    return dict(state, mode='complete')


def delete_checked(api, repo, tag, binary, asset, release_id, expected_binary, expected_sidecar):
    if asset['size'] != 0 or not (asset['state'] == 'uploaded' or starter(asset)):
        raise MetadataError('Refusing to delete a nonempty/unknown asset')
    live = read_release(api, repo, tag)
    targets = [a for a in live['assets'] if a['name'] in (binary, binary + '.sha256')]
    expected = [a for a in (expected_binary, expected_sidecar) if a is not None]
    if (live['id'] != release_id or len(targets) != len(expected)
            or {a['name']: a for a in targets} != {a['name']: a for a in expected}
            or sum(a.get('id') == asset['id'] for a in live['assets']) != 1
            or api.api(f'repos/{repo}/releases/assets/{asset["id"]}') != asset):
        raise MetadataError('Release/asset changed before deletion; rerun')
    api.api(f'repos/{repo}/releases/assets/{asset["id"]}', 'DELETE')


def release_body(tag, repo, build_commit):
    """Source download instructions next to newly published binary releases.

    Does not change any existing Release description or binary. A genuine
    immutable workflow commit must be supplied by GitHub Actions.
    """
    if not re.fullmatch(r'mipsel-v[0-9]+\.[0-9]+\.[0-9]+', tag):
        raise MetadataError('Invalid version for release source pointer')
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repo):
        raise MetadataError('Invalid repository for release source pointer')
    if not re.fullmatch(r'[a-f0-9]{40}', build_commit):
        raise MetadataError('Immutable build commit SHA is required for source pointer')
    upstream = tag.removeprefix('mipsel-')
    return (f'MIPSel softfloat binary from Mihomo upstream {upstream}.\n\n'
            f'## Corresponding source and build instructions\n\n'
            f'- **Upstream tagged source (download):** '
            f'https://github.com/MetaCubeX/mihomo/archive/refs/tags/{upstream}.tar.gz\n'
            f'- **Pinned module graph:** '
            f'https://github.com/MetaCubeX/mihomo/blob/{upstream}/go.mod '
            f'and go.sum (same tag; account for replace directives).\n'
            f'- **Exact builder repository snapshot:** '
            f'https://github.com/{repo}/archive/{build_commit}.zip\n'
            f'- **Build workflow and flags (at build commit):** '
            f'https://github.com/{repo}/blob/{build_commit}/.github/workflows/build-mihomo-mipsel.yml\n'
            f'- **Source availability and limitations:** '
            f'https://github.com/{repo}/blob/{build_commit}/SOURCE-AVAILABILITY.md\n'
            f'- **Third-party module sources:** Go module proxy at versions from '
            f'tagged go.mod/go.sum, with go version -m <binary> cross-check.\n\n'
            f'Binary SHA-256, tagged upstream GPL-3.0 license and collected third-party '
            f'notices are independent release assets. The source map is not a '
            f'legal compliance certification; review GPLv3 §6 and dependency licenses.\n')


def publish(api, repo, tag, binary, directory, planned):
    fresh = inspect(api, repo, tag, binary)
    if fresh != planned:
        raise MetadataError('Release changed since planning; rerun')
    if fresh['mode'] == 'complete':
        return
    path = Path(directory) / binary
    if fresh['mode'] == 'build':
        if not path.is_file() or path.stat().st_size == 0:
            raise MetadataError('No validated local build')
        expected = hashlib.sha256(path.read_bytes()).hexdigest()
        if fresh['release'] is None:
            api.api(f'repos/{repo}/releases', 'POST',
                    {'tag_name': tag, 'name': f'Mihomo {tag[7:]} for MIPSel',
                     'body': release_body(tag, repo, os.environ.get('GITHUB_SHA', ''))})
        if fresh['binary']:
            # inspect only admits a zero-length binary to this branch.
            delete_checked(api, repo, tag, binary, fresh['binary'], fresh['release'],
                           fresh['binary'], fresh['sidecar'])
        api.upload(tag, path)
        # A stale sidecar may belong to an invalid former binary. Verify the
        # newly uploaded binary independently before removing that sidecar.
        release = read_release(api, repo, tag)
        matches = [a for a in release['assets'] if a['name'] == binary]
        if (len(matches) != 1 or matches[0]['state'] != 'uploaded'
                or matches[0]['size'] != path.stat().st_size or digest(matches[0]) != expected
                or (fresh['release'] is not None and release['id'] != fresh['release'])):
            raise MetadataError('Uploaded binary digest/size mismatch')
        release_id, expected_binary = release['id'], matches[0]
        if fresh['sidecar'] and fresh['sidecar']['size'] > 0:
            # A pre-existing valid checksum needs no replacement. A conflict fails closed.
            if inspect(api, repo, tag, binary)['mode'] == 'complete':
                return
    else:
        expected = digest(fresh['binary'])
        release_id, expected_binary = fresh['release'], fresh['binary']
    side = Path(directory) / (binary + '.sha256')
    side.write_bytes(f'{expected}  {binary}\n'.encode())
    if fresh['sidecar']:
        delete_checked(api, repo, tag, binary, fresh['sidecar'], release_id,
                       expected_binary, fresh['sidecar'])
    api.upload(tag, side)
    if inspect(api, repo, tag, binary)['mode'] != 'complete':
        raise MetadataError('Publication remains incomplete')


def main():
    command, tag, binary = sys.argv[1:4]
    if not re.fullmatch(r'mipsel-v[0-9]+\.[0-9]+\.[0-9]+', tag) or binary != 'mihomo-linux-mipsel-softfloat-' + tag[7:]:
        raise MetadataError('Invalid tag/binary identity')
    api, repo = GitHub(), os.environ['GITHUB_REPOSITORY']
    if command == 'plan':
        state = inspect(api, repo, tag, binary)
        Path('release-plan.json').write_text(json.dumps(state))
        with open(os.environ['GITHUB_OUTPUT'], 'a') as output:
            output.write(f'mode={state["mode"]}\nbin_name={binary}\ntag_name={tag}\n')
    elif command == 'publish':
        publish(api, repo, tag, binary, '.', json.loads(Path('release-plan.json').read_text()))
    else:
        raise MetadataError('Invalid command')


if __name__ == '__main__':
    try:
        main()
    except (MetadataError, NotFound, subprocess.CalledProcessError, ValueError, KeyError) as error:
        print(f'Publication refused: {error}', file=sys.stderr)
        sys.exit(2)
