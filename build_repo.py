#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
越狱源 (APT 仓库) 生成器 —— 适用于 Sileo / Zebra / Cydia
扫描 debs/ 下所有 .deb，自动生成 Packages / Packages.gz / Packages.bz2 / Release
纯标准库实现，Windows / macOS / Linux 通用，无需 dpkg。

用法:
    python build_repo.py            # 扫描 debs/ 生成索引
    python build_repo.py --sample   # 先生成一个占位测试包，再生成索引
"""
import os
import sys
import io
import gzip
import bz2
import lzma
import hashlib
import tarfile

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
DEBS_DIR = os.path.join(REPO_DIR, "debs")

# ===================== 仓库元信息（按需修改） =====================
REPO_META = {
    "Origin":      "My Jailbreak Repo",        # 源名称（展示用）
    "Label":       "My Jailbreak Repo",
    "Suite":       "stable",
    "Version":     "1.0",
    "Architectures": "iphoneos-arm iphoneos-arm64",
    "Components":  "main",
    "Description": "我的越狱插件源",
    "Icon":        "https://lyuan216.github.io/MyJailbreakRepo/icon.png",
}
# =================================================================


def parse_deb(path):
    """解析 .deb（ar 归档），取出 control 字段。"""
    with open(path, "rb") as f:
        data = f.read()
    if data[:8] != b"!<arch>\n":
        raise ValueError("%s 不是有效的 .deb" % path)
    offset = 8
    control = None
    while offset + 60 <= len(data):
        name = data[offset:offset + 16].decode("utf-8", "replace").strip()
        size = int(data[offset + 48:offset + 58].strip() or b"0")
        cstart = offset + 60
        content = data[cstart:cstart + size]
        if "control.tar" in name:
            control = content
        offset = cstart + size
        if size % 2 == 1:        # ar 1 字节对齐填充
            offset += 1
    if control is None:
        raise ValueError("%s 缺少 control.tar" % path)
    try:
        tar_bytes = gzip.decompress(control)
    except Exception:
        try:
            tar_bytes = lzma.decompress(control)
        except Exception:
            tar_bytes = control
    fields = {}
    with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode="r:") as tar:
        for m in tar.getmembers():
            base = m.name.replace("./", "").strip("/")
            if base == "control":
                raw = tar.extractfile(m).read().decode("utf-8", "replace")
                for line in raw.splitlines():
                    if ":" in line:
                        k, v = line.split(":", 1)
                        fields[k.strip()] = v.strip()
    return fields


def make_entry(deb_path, rel_name):
    f = parse_deb(deb_path)
    with open(deb_path, "rb") as fh:
        blob = fh.read()
    f["Filename"] = "debs/" + rel_name
    f["Size"] = str(len(blob))
    f["MD5sum"] = hashlib.md5(blob).hexdigest()
    f["SHA256"] = hashlib.sha256(blob).hexdigest()
    if "Architecture" not in f:
        f["Architecture"] = "iphoneos-arm"
    order = ["Package", "Name", "Version", "Architecture", "Description",
             "Depends", "Pre-Depends", "Conflicts", "Replaces", "Breaks",
             "Provides", "Section", "Author", "Maintainer", "Sponsor",
             "Dev", "Website", "Depiction", "Icon", "Tag",
             "Filename", "Size", "MD5sum", "SHA256"]
    lines = [f"{k}: {f[k]}" for k in order if k in f]
    for k, v in f.items():
        if k not in order:
            lines.append(f"{k}: {v}")
    return "\n".join(lines) + "\n"


def glob_debs():
    import glob as g
    return sorted(g.glob(os.path.join(DEBS_DIR, "*.deb")))


def build():
    if not os.path.isdir(DEBS_DIR):
        os.makedirs(DEBS_DIR, exist_ok=True)
    debs = glob_debs()
    if not debs:
        print("[!] debs/ 目录为空，请把你的 .deb 放进去后再运行。")
    entries = []
    for p in debs:
        rel = os.path.basename(p)
        try:
            entries.append(make_entry(p, rel))
            print("[+] %s" % rel)
        except Exception as ex:
            print("[!] 跳过 %s: %s" % (rel, ex))
    packages = "".join(e + "\n" for e in entries)

    with open(os.path.join(REPO_DIR, "Packages"), "w", encoding="utf-8") as f:
        f.write(packages)
    with gzip.open(os.path.join(REPO_DIR, "Packages.gz"), "wt", encoding="utf-8") as f:
        f.write(packages)
    with bz2.open(os.path.join(REPO_DIR, "Packages.bz2"), "wt", encoding="utf-8") as f:
        f.write(packages)
    write_release()
    print("[✓] 生成完成：共 %d 个包" % len(entries))


def write_release():
    lines = []
    for k in ["Origin", "Label", "Icon", "Suite", "Version", "Architectures", "Components", "Description"]:
        lines.append("%s: %s" % (k, REPO_META.get(k, "")))
    files = {}
    for fn in ["Packages", "Packages.gz", "Packages.bz2"]:
        fp = os.path.join(REPO_DIR, fn)
        if os.path.isfile(fp):
            files[fn] = open(fp, "rb").read()
    md5, sha = [], []
    for fn, blob in files.items():
        md5.append(" %s %d %s" % (hashlib.md5(blob).hexdigest(), len(blob), fn))
        sha.append(" %s %d %s" % (hashlib.sha256(blob).hexdigest(), len(blob), fn))
    with open(os.path.join(REPO_DIR, "Release"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
        f.write("MD5Sum:\n" + "\n".join(md5) + "\n")
        f.write("SHA256:\n" + "\n".join(sha) + "\n")


def create_sample_deb():
    os.makedirs(DEBS_DIR, exist_ok=True)
    control = (
        "Package: com.example.demo\n"
        "Name: Demo Tweak (测试包，请删除)\n"
        "Version: 1.0.0\n"
        "Architecture: iphoneos-arm\n"
        "Description: 这是 build_repo.py 生成的占位测试包，用于验证源可正常刷新。上线前请删除并替换为你的真实 .deb。\n"
        "Section: Tweaks\n"
        "Author: You\n"
        "Depends: mobilesubstrate\n"
        "Maintainer: You <you@example.com>\n"
    )
    ctl_buf = io.BytesIO()
    with tarfile.open(fileobj=ctl_buf, mode="w:gz") as tar:
        info = tarfile.TarInfo(name="./control")
        info.size = len(control.encode())
        tar.addfile(info, io.BytesIO(control.encode()))
    data_buf = io.BytesIO()
    with tarfile.open(fileobj=data_buf, mode="w:gz") as tar:
        info = tarfile.TarInfo(name="./")
        info.type = tarfile.DIRTYPE
        info.mode = 0o755
        tar.addfile(info)

    def ar_entry(name, content):
        header = (name.encode().ljust(16, b" ") +
                  b"0".ljust(12, b" ") + b"0".ljust(6, b" ") + b"0".ljust(6, b" ") +
                  b"644".ljust(8, b" ") + str(len(content)).encode().rjust(10, b" ") +
                  b"\x60\x0a")
        return header + content + (b"\n" if len(content) % 2 else b"")

    out = b"!<arch>\n"
    out += ar_entry("debian-binary", b"2.0\n")
    out += ar_entry("control.tar.gz", ctl_buf.getvalue())
    out += ar_entry("data.tar.gz", data_buf.getvalue())
    sample = os.path.join(DEBS_DIR, "com.example.demo_1.0.0_iphoneos-arm.deb")
    with open(sample, "wb") as f:
        f.write(out)
    print("[+] 已生成示例包: %s" % sample)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--sample":
        create_sample_deb()
    build()
