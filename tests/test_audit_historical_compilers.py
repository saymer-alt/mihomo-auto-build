# SPDX-License-Identifier: MIT
import importlib.util
from pathlib import Path
import tempfile
import unittest

root=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location("historic",root/"scripts"/"audit_historical_compilers.py")
mod=importlib.util.module_from_spec(s)
s.loader.exec_module(mod)


class HistoricalBuildinfoTests(unittest.TestCase):
    def test_extracts_only_expected_module_version(self):
        line=("/tmp/mihomo: go1.25.4\n"
              "\tpath\tgithub.com/metacubex/mihomo\n"
              "\tmod\tgithub.com/metacubex/mihomo\tv1.19.25\t\n"
              "\tdep\texample.com/module\tv0.0.1\n")
        self.assertEqual(mod.parse_build_info(line,"v1.19.25"),
                         {"go_version":"go1.25.4","main_module_version":"v1.19.25"})
        with self.assertRaises(ValueError):
            mod.parse_build_info(line,"v1.19.26")

    def test_file_sha256_deterministic(self):
        with tempfile.TemporaryDirectory() as d:
            file=Path(d,"sample")
            file.write_bytes(b"abc")
            self.assertEqual(mod.digest_file(file),
                             "sha256:ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")


if __name__=="__main__":
    unittest.main()
