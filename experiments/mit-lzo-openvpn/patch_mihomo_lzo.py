# SPDX-License-Identifier: MIT
"""EXPERIMENTAL patch in throwaway upstream checkout ONLY.

Replaces OpenVPN's GPLv2 go-lzo call with an MIT-licensed Anchore LZO1X
decoder using bounded output growth. Never writes this repository's
production workflow or an existing Release.
"""
import argparse
from pathlib import Path

OLD_IMPORT = '"bytes"\n'
OLD_MODULE = '"github.com/rasky/go-lzo"'
NEW_MODULE = '"github.com/anchore/go-lzo"'
OLD_CALL = """\t\t\tr := bytes.NewReader(src[1:])
\t\t\tout, err := lzo.Decompress1X(r, len(src)-1, 0)
\t\t\tif err != nil {
\t\t\t\treturn nil, ErrLZODecompress
\t\t\t}
\t\t\treturn out, nil"""
NEW_CALL = """\t\t\t// LZO1X does not encode its decompressed length. Retry on the
\t\t\t// decoder's bounded output-buffer-overrun error, never
\t\t\t// allocating more than 1 MiB for one OpenVPN packet.
\t\t\tcompressed := src[1:]
\t\t\tsize := len(compressed) * 4
\t\t\tif size < 64 {
\t\t\t\tsize = 64
\t\t\t}
\t\t\tif size > 1<<20 {
\t\t\t\tsize = 1 << 20
\t\t\t}
\t\t\tfor {
\t\t\t\tbuf := make([]byte, size)
\t\t\t\tn, err := lzo.Decompress(compressed, buf)
\t\t\t\tif err == nil {
\t\t\t\t\treturn buf[:n], nil
\t\t\t\t}
\t\t\t\tif !errors.Is(err, lzo.ErrOutputOverrun) || size == 1<<20 {
\t\t\t\t\treturn nil, ErrLZODecompress
\t\t\t\t}
\t\t\t\tsize *= 2
\t\t\t\tif size > 1<<20 {
\t\t\t\t\tsize = 1 << 20
\t\t\t\t}
\t\t\t}"""
EXTRA_TEST = """
// TestMITReplacementCompressedFrame uses public LZO1X format bytes:
// five literals followed by the standard end marker.
func TestMITReplacementCompressedFrame(t *testing.T) {
\tframe := []byte{lzoCompressLZO, 22, 'h', 'e', 'l', 'l', 'o', 0x11, 0x00, 0x00}
\tout, err := lzo1xDecompressSafe(frame)
\tif err != nil {
\t\tt.Fatal(err)
\t}
\tif !bytes.Equal(out, []byte("hello")) {
\t\tt.Fatalf("unexpected decompressed data: %q", out)
\t}
}
"""


def only_once(source, old, new, name):
    if source.count(old) != 1:
        raise ValueError(f"Upstream changed: expected exact occurrence of {name}")
    return source.replace(old, new)


def patch(root):
    path = root / "transport" / "openvpn" / "lzo.go"
    source = path.read_text(encoding="utf-8")
    source = only_once(source, OLD_IMPORT, "", "bytes import")
    source = only_once(source, OLD_MODULE, NEW_MODULE, "go-lzo import")
    source = only_once(source, OLD_CALL, NEW_CALL, "go-lzo decompress call")
    if "rasky/go-lzo" in source or "bytes." in source:
        raise ValueError("Unexpected remaining old GPL implementation")
    path.write_text(source, encoding="utf-8")
    tests = root / "transport" / "openvpn" / "lzo_test.go"
    value = tests.read_text(encoding="utf-8")
    if "TestMITReplacementCompressedFrame" in value:
        raise ValueError("Test already present; refuse uncertain rerun")
    tests.write_text(value.rstrip() + "\n" + EXTRA_TEST, encoding="utf-8")
    print("Temporary upstream OpenVPN code and compressed fixture patched; release workflow untouched")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    patch(args.root)


if __name__ == "__main__":
    main()
