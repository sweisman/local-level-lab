# Public website

The site at **locallevellab.com** uses the root README as its homepage. Linked
Markdown documents become subpages with the same source hierarchy. Images are
copied into the site; CSVs, scientific artifacts and code link to GitHub. Editing
the public Markdown updates both the repository and the website on the next
published push. The numerical analysis is separate from the website build.

## Build and check locally

```sh
~/venv/bin/python -m pip install -r website/requirements.txt
~/venv/bin/python website/build.py --output /tmp/local-level-lab-site
~/venv/bin/python -m pytest website/tests -q
~/venv/bin/python -m http.server 8000 --directory /tmp/local-level-lab-site
```

Open `http://localhost:8000`. The generated site includes a build report, sitemap,
responsive tables, equations and Mermaid diagrams. Equations and diagrams load
pinned browser libraries; document text and navigation work without JavaScript.
The builder follows explicit documentation links and never inventories local
data directories. It does not run analysis, change measurements or rewrite source
documents. Rebuild into a fresh output directory.

## Publishing

The `pages` GitHub Actions workflow builds on pushes to `main` affecting public
Markdown, documentation images or website files. It also supports a manually
requested deployment. Pull requests build and test without publishing.

GitHub Pages uses the **GitHub Actions** publishing source and the custom domain
`locallevellab.com`. DNS is managed separately at the domain registrar. HTTPS can
be enforced once GitHub validates the DNS records and provisions its certificate.
Site publication does not host the upload server or participant recordings.
