#!/usr/bin/env python3
"""x64 gates 1-3 for agy 1.4.x (signatures extracted from Milordick/rust-antigravity-patcher
targets/agy.rs: CLI eligibility, hasValidAuth, print-mode eligibility)."""
import re, struct, sys, mmap, os

PATH = os.path.expanduser("~/.local/bin/agy.real")

GATE1 = (rb"\x48\x85\xc0\x0f\x84....\x80\x78\x08\x00\x0f\x85....",
         9, 4, b"\x48\x85\xc0\x90", "eligibility screen off (x64)")
GATE2 = (rb"\x80\x78\x08\x00\x74.\x48\x8b.[\x24].\x48\x89.\x60",
         0, 6, b"\xc6\x40\x08\x01\x90\x90", "hasValidAuth=true (x64)")
GATE3 = (rb"\x48\x85\xc0\x0f\x85....\x48\x85\xc9\x0f\x84....\x80\x79\x08\x00\x0f\x85....",
         18, 4, b"\x48\x85\xc9\x90", "print-mode eligibility rcx off (x64)")

def exec_bounds(f):
    f.seek(0); data = f.read(64)
    assert data[:4] == b"\x7fELF"
    e_phoff = struct.unpack_from("<Q", data, 0x20)[0]
    e_phentsize = struct.unpack_from("<H", data, 0x36)[0]
    e_phnum = struct.unpack_from("<H", data, 0x38)[0]
    segs = []
    for i in range(e_phnum):
        f.seek(e_phoff + i * e_phentsize)
        ph = f.read(e_phentsize)
        p_type, p_flags = struct.unpack_from("<II", ph, 0)
        p_offset = struct.unpack_from("<Q", ph, 8)[0]
        p_filesz = struct.unpack_from("<Q", ph, 32)[0]
        if p_type == 1 and (p_flags & 1):  # PT_LOAD, PF_X
            segs.append((p_offset, p_offset + p_filesz))
    return segs

def main(apply=True):
    with open(PATH, "r+b") as f:
        mm = mmap.mmap(f.fileno(), 0)
        segs = exec_bounds(f)
        patches = []
        for pat, fix_off, fix_len, fix_bytes, name in (GATE1, GATE2, GATE3):
            hits = []
            for s, e in segs:
                for m in re.finditer(pat, mm[s:e], re.S):
                    hits.append(s + m.start())
                if len(hits) > 1: break
            if not hits:
                print(f"[!] {name}: сигнатура не найдена — пропуск"); continue
            off = hits[0]
            if mm[off + fix_off: off + fix_off + fix_len] == fix_bytes:
                print(f"[=] {name}: уже пропатчен @ {off:#x}"); continue
            state = mm[off:off + 20].hex()
            print(f"[+] {name}: @ {off:#x} (шаблон {state})")
            patches.append((off + fix_off, fix_off, fix_len, fix_bytes, name, off))
        if not patches:
            print("нет изменений"); return
        if not apply:
            return
        for off, full_off, ln, fx, name, gate_off in patches:
            f.seek(gate_off)
            mm[off:off + ln] = fx
            print(f"[ok] {name}: вписано {fx.hex()} @ {off:#x}")
        mm.flush()
        # verify
        mm.seek(0)
        for pat, fix_off, fix_len, fix_bytes, name in (GATE1, GATE2, GATE3):
            off = None
            for s, e in segs:
                m = re.search(pat, mm[s:e], re.S)
                if m: off = s + m.start(); break
            if off is not None and mm[off + fix_off: off + fix_off + fix_len] != fix_bytes:
                print(f"[X] {name}: верификация не сошлась!"); sys.exit(1)
        print("верификация после записи: ok")

if __name__ == "__main__":
    main(apply="--dry" not in sys.argv)
