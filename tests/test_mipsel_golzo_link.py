# SPDX-License-Identifier: MIT
"""Offline tests for nonpublishing Go package import/linker evidence audit."""
import importlib.util
import json
from pathlib import Path
import unittest

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "audit", root / "scripts" / "audit_mipsel_golzo_link.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class GoLinkageAnalysisTest(unittest.TestCase):
    def setUp(self):
        self.main = "github.com/metacubex/mihomo"
        self.adapter = "example.com/adapter"
        self.lzo = audit.TARGET
        self.packages = audit.parse_go_list("".join(json.dumps(x) + "\n" for x in [
            {"ImportPath":self.main,"Module":{"Path":self.main},
             "Imports":[self.adapter]},
            {"ImportPath":self.adapter,"Module":{"Path":"example.com/adapter"},
             "Imports":[self.lzo]},
            {"ImportPath":self.lzo,"Module":{"Path":self.lzo},
             "Imports":["unsafe"]},
            {"ImportPath":"unsafe","Imports":[]}
        ]))

    def test_import_chain_and_no_false_linkage(self):
        self.assertEqual(audit.shortest_chain(self.packages, self.main),
                         [self.main, self.adapter, self.lzo])
        result = audit.report(self.packages, [], self.main)
        self.assertEqual(result["target_package_count"], 1)
        self.assertEqual(result["unstripped_linker_symbol_count"], 0)
        self.assertIn("NOT a byte-identical", result["symbol_evidence_note"])

    def test_symbol_matching_real_function_only(self):
        nm = (
            "000a2b3c      40 T github.com/rasky/go-lzo.Decompress1X\n"
            "000a2b5c      16 t github.com/rasky/go-lzo.helper\n"
            "000a2b6c      40 T github.com/rasky/go-lzo-other.NotThePackage\n"
            "000a2b7c      16 T another.PkgName\n")
        self.assertEqual(len(audit.symbol_names(nm)), 2)

    def test_parser_rejects_duplicate_or_bad_object(self):
        with self.assertRaises(ValueError):
            audit.parse_go_list('{"ImportPath":"example"}\n{"ImportPath":"example"}\n')
        with self.assertRaises(ValueError):
            audit.parse_go_list('{"bad":42}')

    def test_absent_module_not_inferred(self):
        for path in (self.adapter,self.lzo):
            self.packages.pop(path)
        self.packages[self.main]["imports"] = []
        self.assertEqual(audit.shortest_chain(self.packages,self.main), [])


if __name__ == "__main__":
    unittest.main()
