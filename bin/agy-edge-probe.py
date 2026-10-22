#!/usr/bin/env python3
# Поиск живых "анблок"-краёв для Google-доменов Antigravity:
# UDP/53 опрос провайдеров подмены + DoH + боевая HTTPS-проба (валидный Google-сертификат).
import socket, struct, subprocess, time, json, sys, binascii

DOMAINS = [
    "daily-cloudcode-pa.googleapis.com",
    "generativelanguage.googleapis.com",
]
UDP_PROVIDERS = ["45.155.204.190", "37.230.192.51", "83.220.169.155",
                 "212.109.195.93", "195.133.25.16"]
DOH = [
    ("dns.geohide.ru", ["37.230.192.51", "45.155.204.190"]),
    ("dns.comss.one", ["83.220.169.155", "212.109.195.93", "195.133.25.16"]),
    ("dns.dns-ai.ru", ["192.144.59.14", "186.246.49.127", "185.251.90.181"]),
]

def dns_query_wire(name):
    q = b"".join(bytes([len(p)]) + p.encode() for p in name.split(".")) + b"\x00"
    hdr = struct.pack(">HHHHHH", 0x1234, 0x0100, 1, 0, 0, 0)
    return hdr + q + struct.pack(">HH", 1, 1)

def parse_a(packet):
    try:
        _, flags, qd, an, _, _ = struct.unpack(">HHHHHH", packet[:12])
        if not (flags & 0x8000) and not an: return []
        i = 12
        for _ in range(qd):
            while packet[i] & 0xC0 != 0xC0 and packet[i] != 0: i += packet[i] + 1
            if packet[i] == 0: i += 1
            else: i += 2
            i += 4
        out = []
        for _ in range(an):
            while packet[i] & 0xC0 != 0xC0 and packet[i] != 0: i += packet[i] + 1
            if packet[i] == 0: i += 1
            else: i += 2
            rtype, _, _, rdlen = struct.unpack(">HHIH", packet[i:i+10]); i += 10
            if rtype == 1 and rdlen == 4: out.append(".".join(map(str, packet[i:i+4])))
            i += rdlen
        return out
    except Exception:
        return []

def udp_answers(server, name, timeout=3):
    pkt = dns_query_wire(name)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.settimeout(timeout)
    try:
        s.sendto(pkt, (server, 53)); data, _ = s.recvfrom(4096)
    except Exception:
        return []
    return parse_a(data)

def doh_answers(host, ip, name):
    import base64
    q = base64.urlsafe_b64encode(dns_query_wire(name)).decode().rstrip("=")
    for extra in ([], ["--http2"], ["--http1.1"]):
        for urlfmt in ("https://{h}/dns-query?dns={q}", "https://{h}/resolve?dns={q}&type=A"):
            url = urlfmt.format(h=host, q=q)
            r = subprocess.run(
                ["curl", "-s", "--max-time", "6", *extra, "--resolve", f"{host}:443:{ip}",
                 "-H", "accept: application/dns-message", url],
                capture_output=True)
            if r.returncode == 0 and r.stdout:
                ips = parse_a(r.stdout)
                if ips: return ips
    return []

def probe(domain, ip):
    r = subprocess.run(["curl", "-s", "--max-time", "6", "--resolve", f"{domain}:443:{ip}",
                        f"https://{domain}/", "-o", "/dev/null",
                        "-w", "%{http_code} %{time_total}"], capture_output=True, text=True)
    if r.returncode != 0: return None
    parts = r.stdout.strip().split()
    if not parts: return None
    code = parts[0]
    if code[0] in "234": return float(parts[1])
    return None

def main():
    results = {}
    for dom in DOMAINS:
        ref_raw = subprocess.run(
            ["curl", "-s", "--max-time", "6",
             f"https://dns.google/resolve?name={dom}&type=A"],
            capture_output=True, text=True).stdout
        ref = [a["data"] for a in (json.loads(ref_raw).get("Answer") or []) if a.get("type") == 1]
        ref16 = {ip.rsplit(".", 2)[0] for ip in ref if ip.count(".") == 3}
        print(f"== {dom}  эталон: {sorted(ref16)}")
        cands = set()
        for srv in UDP_PROVIDERS:
            ans = udp_answers(srv, dom)
            sub = [ip for ip in ans if ip.count(".") == 3 and ip.rsplit(".", 2)[0] not in ref16]
            if sub: print(f"   UDP @{srv}: подмена {sub}")
            cands.update(sub)
        for h, ips in DOH:
            got = []
            for ip in ips:
                resp = doh_answers(h, ip, dom)
                if resp: got = [a for a in resp if a.count(".") == 3 and a.rsplit(".", 2)[0] not in ref16]; break
            if got: print(f"   DoH @{h}: подмена {got}")
            cands.update(a for a in got if a.count(".") == 3)
        scored = []
        for ip in sorted(cands):
            t = probe(dom, ip)
            if t is None:
                print(f"   проба {ip}: НЕЖИВОЙ")
            else:
                print(f"   проба {ip}: ЖИВОЙ {t:.2f}s")
                scored.append((t, ip))
        results[dom] = [ip for _, ip in sorted(scored)[:2]]
        print(f"   => пин для {dom}: {results[dom]}")
    print("\nPIN_MAP:", "|".join(f"{d}:{','.join(i)}" for d, i in results.items() if i), "|")

if __name__ == "__main__":
    main()
