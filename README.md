# 越狱源（APT 仓库）脚手架

给 Sileo / Zebra / Cydia 用的包管理源。把 `.deb` 丢进 `debs/`，跑一条命令，就能生成可被包管理器刷新的索引。

## 目录结构

```
jailbreak-repo/
├── build_repo.py            # 索引生成器（改完 .deb 就跑它）
├── Packages                 # 生成的索引（明文）
├── Packages.gz             # 生成的索引（gzip）
├── Packages.bz2            # 生成的索引（bzip2）
├── Release                 # 生成的仓库描述
├── .nojekyll               # 让 GitHub Pages 不处理
├── debs/                   # 把你的 .deb 放这里
│   └── *.deb
└── depictions/             # 可选：包的详情展示页
    └── com.example.demo/
        └── index.html
```

## 你要做的 3 步

### 1. 放入你的插件
把编译好的 `.deb`（theos 产物，命名建议 `com.你的id.插件名_版本_iphoneos-arm.deb`）放进 `debs/`。
删掉里面的 `com.example.demo_*.deb` 示例包。

### 2. 生成索引
```bash
python build_repo.py
```
会重新生成 `Packages` / `Packages.gz` / `Packages.bz2` / `Release`。

### 3. 托管 + 添加源
必须能通过 **HTTPS** 访问到根目录下的 `Packages` 和 `Release`。三种方式任选：

- **GitHub Pages（最省事）**：把这个文件夹推到仓库，仓库 Settings → Pages 选分支根目录。源地址就是 `https://<用户名>.github.io/<仓库名>/`
- **任意静态空间**：Vercel / Netlify / 对象存储 / 自己的 Nginx，把整个文件夹传上去。
- **本地测试**：`python -m http.server 8080`，手机和电脑同一 WiFi 时源地址填 `http://<电脑IP>:8080/`（注意：部分管理器要求 HTTPS，本地仅用于验证）。

然后在 Sileo / Zebra / Cydia 里「添加源 / Add Source」，粘贴上面的地址即可刷新看到你的插件。

## 可选：包详情页（Depiction）
在 `depictions/<PackageID>/index.html` 写展示页，并在 `.deb` 的 control 里加：
```
Depiction: https://你的源地址/depictions/<PackageID>/
```
包管理器点开包就会显示该页（功能介绍、截图、捐赠链接等）。

## 改仓库名 / 描述
编辑 `build_repo.py` 顶部的 `REPO_META` 字典（Origin / Label / Description 等）。
