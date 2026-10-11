// SPDX-License-Identifier: MIT
// Experimental cleanly licensed OpenVPN LZO1X decompression compatibility probe.
// This file is not used by the released Mihomo build.
package lzoprobe

import (
    "bytes"
    "errors"
    "testing"

    decoder "github.com/anchore/go-lzo"
    encoder "github.com/woozymasta/lzo"
)

const (
    noCompression = 0xFA
    lzoCompressed = 0x66
    maxDecompressedPacket = 1 << 20
)

var (
    errBadFrame = errors.New("OpenVPN LZO: malformed or unsupported frame")
    errSizeCap = errors.New("OpenVPN LZO: decompression output limit")
)

func decodeOpenVPNLZOFrame(src []byte) ([]byte,error) {
    if len(src)==0 { return nil,errBadFrame }
    switch src[0] {
    case noCompression:
        return src[1:],nil
    case lzoCompressed:
        compressed:=src[1:]
        size:=len(compressed)*4
        if size<64 { size=64 }
        if size>maxDecompressedPacket { size=maxDecompressedPacket }
        for {
            dst:=make([]byte,size)
            n,err:=decoder.Decompress(compressed,dst)
            if err==nil {return dst[:n],nil}
            if !errors.Is(err,decoder.ErrOutputOverrun) { return nil,err }
            if size==maxDecompressedPacket {return nil,errSizeCap}
            size*=2
            if size>maxDecompressedPacket {size=maxDecompressedPacket}
        }
    default:
        return nil,errBadFrame
    }
}

func TestOpenVPNUncompressedFrame(t *testing.T){
    message:=[]byte("OpenVPN passthrough header 0xFA")
    decoded,err:=decodeOpenVPNLZOFrame(append([]byte{noCompression},message...))
    if err!=nil || !bytes.Equal(decoded,message) {t.Fatalf("passthrough: %v",err)}
}

func TestLZO1XCompressedOpenVPNFrames(t *testing.T){
    cases:=[][]byte{
        []byte("A"),
        []byte("OpenVPN LZO packet with repeated data!"),
        bytes.Repeat([]byte("ABCDABCDABCD--"),256),
        bytes.Repeat([]byte("AAABBBCCCDDDEEE"),3277),
    }
    for i,original:=range cases {
        compressed,err:=encoder.Compress(original,nil)
        if err!=nil {t.Fatalf("compress case %d: %v",i,err)}
        decoded,err:=decodeOpenVPNLZOFrame(append([]byte{lzoCompressed},compressed...))
        if err!=nil || !bytes.Equal(decoded,original) {
            t.Fatalf("OpenVPN LZO frame %d (%d bytes): %v, match=%t",i,len(original),err,bytes.Equal(decoded,original))
        }
    }
}

func TestLZOBoundedExpansion(t *testing.T){
    original:=bytes.Repeat([]byte("A"),maxDecompressedPacket+1)
    compressed,err:=encoder.Compress(original,nil)
    if err!=nil {t.Fatal(err)}
    _,err=decodeOpenVPNLZOFrame(append([]byte{lzoCompressed},compressed...))
    if !errors.Is(err,errSizeCap) {t.Fatalf("expected bounded expansion rejection, got %v",err)}
}

func TestStaticLZO1XFixtureFromFormat(t *testing.T){
    // Format-level fixture: 5 initial literal bytes, then 0x11 0x00 0x00
    // end marker. Independent of any GPL-licensed compression implementation.
    frame:=[]byte{lzoCompressed,22,'h','e','l','l','o',0x11,0x00,0x00}
    decoded,err:=decodeOpenVPNLZOFrame(frame)
    if err!=nil || !bytes.Equal(decoded,[]byte("hello")) {
        t.Fatalf("static LZO1X fixture: %v decoded=%q",err,decoded)
    }
}

func TestInvalidOpenVPNFraming(t *testing.T){
    for _,b:=range [][]byte{nil,{}, {0x42},{lzoCompressed,0x00}} {
        if _,err:=decodeOpenVPNLZOFrame(b);err==nil {
            t.Fatalf("invalid frame unexpectedly accepted: %v",b)
        }
    }
}
