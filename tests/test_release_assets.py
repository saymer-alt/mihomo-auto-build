import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('release_assets', Path(__file__).resolve().parents[1] / 'scripts/release_assets.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
BIN = 'mihomo-linux-mipsel-softfloat-v1.19.32'
TAG = 'mipsel-v1.19.32'
DATA = b'healthy existing binary'


class Fake:
    def __init__(self, binary=DATA, side=False):
        self.release = {'id': 1, 'tag_name': TAG, 'draft': False, 'assets': []}
        self.content = {}
        self.calls = []
        self.fail_upload = False
        if binary is not None:
            self.add(BIN, binary)
        if side:
            self.add(BIN+'.sha256', hashlib.sha256(binary).hexdigest().encode()+b'  '+BIN.encode()+b'\n')

    def add(self, name, data):
        identity = max(self.content, default=10)+1
        self.content[identity] = data
        self.release['assets'].append({'id': identity, 'name': name, 'state': 'uploaded',
                                      'size': len(data), 'digest': 'sha256:'+hashlib.sha256(data).hexdigest()})

    def api(self, path, method='GET', fields=None, raw=False):
        self.calls.append((method, path))
        if method == 'DELETE':
            identity = int(path.rsplit('/',1)[1])
            self.release['assets'] = [a for a in self.release['assets'] if a['id'] != identity]
            return None
        if raw:
            return self.content[int(path.rsplit('/',1)[1])]
        if not self.release:
            raise m.NotFound(path)
        return copy.deepcopy(self.release)

    def upload(self, tag, path):
        self.calls.append(('UPLOAD', path.name))
        if self.fail_upload:
            raise subprocess.CalledProcessError(1, 'upload')
        if any(a['name'] == path.name for a in self.release['assets']):
            raise m.MetadataError('conflict')
        self.add(path.name, path.read_bytes())


class Tests(unittest.TestCase):
    def inspect(self, api):
        return m.inspect(api, 'owner/repo', TAG, BIN)

    def publish(self, api, state=None):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, BIN).write_bytes(DATA)
            m.publish(api, 'owner/repo', TAG, BIN, directory, state or self.inspect(api))

    def test_complete(self):
        api = Fake(side=True)
        self.assertEqual(self.inspect(api)['mode'], 'complete')
        self.publish(api)
        self.assertFalse(any(c[0] in ['DELETE','UPLOAD'] for c in api.calls))

    def test_checksum_only_and_rerun(self):
        api = Fake()
        identity = api.release['assets'][0]['id']
        self.assertEqual(self.inspect(api)['mode'], 'checksum')
        self.publish(api)
        self.assertEqual(self.inspect(api)['mode'], 'complete')
        self.assertEqual(api.release['assets'][0]['id'], identity)
        self.assertNotIn(('UPLOAD', BIN), api.calls)
        self.assertFalse(any(c[0] == 'DELETE' for c in api.calls))
        self.publish(api)

    def test_failed_sidecar_upload_preserves_binary_then_retries(self):
        api = Fake(); original = copy.deepcopy(api.release)
        api.fail_upload = True
        with self.assertRaises(subprocess.CalledProcessError): self.publish(api)
        self.assertEqual(api.release, original)
        api.fail_upload = False
        self.publish(api)
        self.assertEqual(self.inspect(api)['mode'], 'complete')

    def test_missing_and_zero_binary(self):
        for data in [None, b'']:
            api = Fake(binary=data)
            self.assertEqual(self.inspect(api)['mode'], 'build')
            self.publish(api)
            self.assertEqual(self.inspect(api)['mode'], 'complete')

    def test_checksum_mismatch_and_corrupt_metadata_fail_closed(self):
        for mutation in ['checksum', 'digest', 'size', 'duplicate', 'tag']:
            api = Fake(side=True)
            if mutation == 'checksum':
                api.release['assets'].pop()
                api.add(BIN+'.sha256', b'0'*64+b'  '+BIN.encode()+b'\n')
            elif mutation == 'digest': api.release['assets'][1]['digest'] = 'sha256:'+'0'*64
            elif mutation == 'size': api.release['assets'][0]['size'] = '42'
            elif mutation == 'duplicate': api.release['assets'].append(api.release['assets'][0])
            else: api.release['tag_name'] = 'wrong'
            with self.assertRaises(m.MetadataError): self.inspect(api)
            self.assertFalse(any(c[0] == 'DELETE' for c in api.calls))

    def test_partial_publication_failure_then_resume(self):
        api = Fake(binary=None)
        old_upload = api.upload
        def upload(tag, path):
            if path.name.endswith('.sha256'): raise subprocess.CalledProcessError(1, 'upload')
            old_upload(tag, path)
        api.upload = upload
        with self.assertRaises(subprocess.CalledProcessError): self.publish(api)
        identity = api.release['assets'][0]['id']
        api.upload = old_upload
        self.publish(api)
        self.assertEqual(api.release['assets'][0]['id'], identity)

    def test_failed_binary_upload_then_retry(self):
        api = Fake(binary=None); api.fail_upload = True
        with self.assertRaises(subprocess.CalledProcessError): self.publish(api)
        self.assertEqual(api.release['assets'], [])
        api.fail_upload = False
        self.publish(api)
        self.assertEqual(self.inspect(api)['mode'], 'complete')

    def test_zero_checksum_and_missing_digest(self):
        api = Fake(); api.add(BIN+'.sha256', b'')
        self.assertEqual(self.inspect(api)['mode'], 'checksum')
        self.publish(api)
        self.assertNotIn(('UPLOAD', BIN), api.calls)
        api = Fake(); api.release['assets'][0].pop('digest')
        with self.assertRaises(m.MetadataError): self.inspect(api)

    def test_concurrent_change_refused(self):
        api = Fake(); state = self.inspect(api); api.add('foreign',b'1')
        # Changes to unrelated assets are allowed; changes to target are not.
        api.release['assets'][0]['id'] = 99
        with self.assertRaises(m.MetadataError): self.publish(api,state)

    def test_http_and_invalid_json_are_not_missing(self):
        for status in [429,500,503]:
            result = subprocess.CompletedProcess([],1,b'',f'gh: failed (HTTP {status})'.encode())
            with patch.object(subprocess,'run',return_value=result):
                with self.assertRaises(m.MetadataError): m.GitHub().api('repos/o/r/releases/tags/tag')
        with patch.object(subprocess,'run',return_value=subprocess.CompletedProcess([],0,b'not json',b'')):
            with self.assertRaises(m.MetadataError): m.GitHub().api('x')
        with patch.object(subprocess,'run',return_value=subprocess.CompletedProcess([],1,b'',b'gh: Not Found (HTTP 404)')):
            with self.assertRaises(m.NotFound): m.GitHub().api('x')


if __name__ == '__main__': unittest.main()
