# SPDX-License-Identifier: MIT
"""Server-side upload leftovers, using the real release state machine."""
import copy
import hashlib
from pathlib import Path
import subprocess
import tempfile
import unittest

from test_release_assets import BIN, DATA, Fake, TAG, m


class Server(Fake):
    def __init__(self, binary=DATA):
        super().__init__(binary=binary)
        self.add('foreign.asset', b'preserve foreign data')
        self.fault = None
        self.fail_delete = False
        self.object_change = None

    def upload(self, tag, path):
        if self.fault == ('starter', path.name):
            self.release['assets'].append(dict(id=99, name=path.name, state='starter', size=0, digest=None))
            raise subprocess.CalledProcessError(1, 'HTTP 502 after starter created')
        super().upload(tag, path)
        if self.fault == ('ack', path.name):
            raise subprocess.CalledProcessError(1, 'response lost after healthy commit')

    def api(self, path, method='GET', fields=None, raw=False):
        if method == 'DELETE' and self.fail_delete:
            raise m.MetadataError('HTTP 503 DELETE')
        if method == 'GET' and not raw and '/releases/assets/' in path and self.object_change:
            target = next(a for a in self.release['assets'] if a['id'] == int(path.rsplit('/', 1)[1]))
            target.update(self.object_change)
            return copy.deepcopy(target)
        return super().api(path, method, fields, raw)


class StarterRecovery(unittest.TestCase):
    def inspect(self, api):
        return m.inspect(api, 'owner/repo', TAG, BIN)

    def publish(self, api):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, BIN).write_bytes(DATA)
            m.publish(api, 'owner/repo', TAG, BIN, directory, self.inspect(api))

    def failed_upload(self, target):
        api = Server(binary=None if target == BIN else DATA)
        baseline = copy.deepcopy(api.release['assets'])
        api.fault = ('starter', target)
        with self.assertRaises(subprocess.CalledProcessError): self.publish(api)
        self.assertFalse(any(c[0] == 'DELETE' for c in api.calls))
        api.fault = None
        return api, baseline

    def test_binary_and_checksum_server_starter_recovery_twice(self):
        for target in (BIN, BIN+'.sha256'):
            with self.subTest(target=target):
                api, baseline = self.failed_upload(target)
                self.publish(api)
                self.assertTrue(all(a in api.release['assets'] for a in baseline))
                self.assertEqual(self.inspect(api)['mode'], 'complete')
                after = copy.deepcopy(api.release['assets'])
                self.publish(api)
                self.assertEqual(after, api.release['assets'])
                self.assertEqual([c for c in api.calls if c[0] == 'DELETE'],
                                 [('DELETE', 'repos/owner/repo/releases/assets/99')])
                if target.endswith('.sha256'): self.assertNotIn(('UPLOAD', BIN), api.calls)

    def test_delete_failure_then_retry_preserves_healthy_and_foreign(self):
        for target in (BIN, BIN+'.sha256'):
            api, baseline = self.failed_upload(target)
            api.fail_delete = True
            before = copy.deepcopy(api.release['assets'])
            with self.assertRaises(m.MetadataError): self.publish(api)
            self.assertEqual(before, api.release['assets'])
            api.fail_delete = False
            self.publish(api); self.publish(api)
            self.assertTrue(all(a in api.release['assets'] for a in baseline))

    def test_lost_ack_after_committed_binary_or_checksum_reuses_ids(self):
        for target in (BIN, BIN+'.sha256'):
            api = Server(binary=None if target == BIN else DATA)
            api.fault = ('ack', target)
            with self.assertRaises(subprocess.CalledProcessError): self.publish(api)
            committed = copy.deepcopy(api.release['assets'])
            api.fault = None
            self.publish(api); self.publish(api)
            self.assertTrue(all(a in api.release['assets'] for a in committed))
            self.assertFalse(any(c[0] == 'DELETE' for c in api.calls))

    def test_object_changes_before_delete_are_refused(self):
        for target in (BIN, BIN+'.sha256'):
            for change in (dict(state='uploaded', size=len(DATA), digest='sha256:'+'a'*64),
                           dict(id=199), dict(name='foreign.asset'), dict(size=1)):
                api, baseline = self.failed_upload(target)
                api.object_change = change
                with self.assertRaises(m.MetadataError): self.publish(api)
                self.assertFalse(any(c[0] == 'DELETE' for c in api.calls))
                self.assertTrue(all(a in api.release['assets'] for a in baseline))

    def test_release_identity_or_target_changes_at_deletion_guard(self):
        for target in (BIN, BIN+'.sha256'):
            for change in ('tag', 'release', 'asset'):
                api, baseline = self.failed_upload(target)
                original = api.api
                reads = 0
                def changed(path, method='GET', fields=None, raw=False):
                    nonlocal reads
                    if '/releases/tags/' in path:
                        reads += 1
                        if reads == 3:  # planning, admission, immediate pre-DELETE snapshot
                            if change == 'tag': api.release['tag_name'] = 'foreign'
                            elif change == 'release': api.release['id'] = 142
                            else: api.release['assets'][-1]['id'] = 199
                    return original(path, method, fields, raw)
                api.api = changed
                with self.assertRaises(m.MetadataError): self.publish(api)
                self.assertFalse(any(c[0] == 'DELETE' for c in api.calls))
                self.assertTrue(all(a in api.release['assets'] for a in baseline))

    def test_invalid_and_ambiguous_starters_fail_closed(self):
        for target in (BIN, BIN+'.sha256'):
            for change in (dict(id=0), dict(id=True), dict(size=1), dict(size=False),
                           dict(state='unknown'), dict(digest='sha256:'+'a'*64)):
                api, _ = self.failed_upload(target)
                api.release['assets'][-1].update(change)
                with self.assertRaises(m.MetadataError): self.publish(api)
                self.assertFalse(any(c[0] == 'DELETE' for c in api.calls))
            for duplicate in ('name', 'id'):
                api, _ = self.failed_upload(target)
                a = api.release['assets'][-1]
                api.release['assets'].append(dict(a, **({'id':199} if duplicate == 'name' else {'name':'foreign.zero'})))
                with self.assertRaises(m.MetadataError): self.publish(api)
                self.assertFalse(any(c[0] == 'DELETE' for c in api.calls))

    def test_binary_and_sidecar_starters_allow_reverse_asset_order(self):
        api = Server(binary=None)
        api.release['assets'] += [dict(id=98, name=BIN+'.sha256', state='starter', size=0, digest=None),
                                  dict(id=99, name=BIN, state='starter', size=0, digest=None)]
        self.publish(api); self.publish(api)
        self.assertEqual(self.inspect(api)['mode'], 'complete')

    def test_existing_healthy_checksum_is_preserved_during_binary_recovery(self):
        for valid in (True, False):
            api, baseline = self.failed_upload(BIN)
            checksum = hashlib.sha256(DATA).hexdigest() if valid else '0'*64
            api.add(BIN+'.sha256', f'{checksum}  {BIN}\n'.encode())
            sidecar = copy.deepcopy(api.release['assets'][-1])
            if valid:
                self.publish(api); self.publish(api)
                self.assertEqual(self.inspect(api)['mode'], 'complete')
            else:
                with self.assertRaises(m.MetadataError): self.publish(api)
            self.assertIn(sidecar, api.release['assets'])
            self.assertNotIn(('UPLOAD', BIN+'.sha256'), api.calls)
            self.assertEqual([c for c in api.calls if c[0] == 'DELETE'],
                             [('DELETE','repos/owner/repo/releases/assets/99')])

    def test_object_get_failure_stops_before_delete(self):
        for target in (BIN, BIN+'.sha256'):
            api, baseline = self.failed_upload(target)
            before = copy.deepcopy(api.release['assets'])
            original = api.api
            def failed(path, method='GET', fields=None, raw=False):
                if method == 'GET' and not raw and '/releases/assets/' in path:
                    raise m.MetadataError('HTTP 429 object GET')
                return original(path, method, fields, raw)
            api.api = failed
            with self.assertRaises(m.MetadataError): self.publish(api)
            self.assertEqual(before, api.release['assets'])
            self.assertFalse(any(c[0] == 'DELETE' for c in api.calls))

    def test_lost_delete_ack_can_be_retried(self):
        for target in (BIN, BIN+'.sha256'):
            api, baseline = self.failed_upload(target)
            original = api.api
            def lost_ack(path, method='GET', fields=None, raw=False):
                result = original(path,method,fields,raw)
                if method == 'DELETE': raise m.MetadataError('DELETE committed, response lost')
                return result
            api.api = lost_ack
            with self.assertRaises(m.MetadataError): self.publish(api)
            api.api = original
            self.publish(api); self.publish(api)
            self.assertTrue(all(a in api.release['assets'] for a in baseline))
            self.assertEqual([c for c in api.calls if c[0]=='DELETE'],
                             [('DELETE','repos/owner/repo/releases/assets/99')])
