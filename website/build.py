# SPDX-License-Identifier: AGPL-3.0-or-later
"""Render explicitly linked public Markdown; never scan the research corpus."""
import argparse
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path, PurePosixPath
import posixpath
import re
import shutil
from urllib.parse import quote, unquote, urlsplit, urlunsplit

import markdown
from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor

HERE=Path(__file__).resolve().parent
REPOSITORY='https://github.com/sweisman/local-level-lab'
DOMAIN='https://locallevellab.com'
NAVIGATION=(('Home','README.md'),
            ('Findings','docs/ilvis0-position-stability-trial-20261013/FINDINGS.md'),
            ('Method','docs/METHODOLOGY.md'),
            ('Flight stretches','docs/ilvis0-position-stability-trial-20261013/STRETCHES.md'),
            ('Ground experiment','docs/STATIONARY.md'))
IMAGES={'.png','.jpg','.jpeg','.gif','.svg','.webp','.ico'}


def slug(text,separator):
    text=re.sub('<[^>]+>','',html.unescape(text)).lower()
    return re.sub(r'\s+',separator,re.sub(r'[^\w\-\s]','',text)).strip(separator)


class MathPreprocessor(Preprocessor):
    def run(self,lines):
        text='\n'.join(lines)
        # Fenced code was already stashed by Markdown. Protect inline code too.
        literals=[]
        def literal(match):
            literals.append(match[0]);return f'\x02LLLCODE{len(literals)-1}\x03'
        text=re.sub(r'(`+)(.+?)\1',literal,text,flags=re.S)
        def store(match,display=False):
            expression=match[1]
            tag='div' if display else 'span'
            delimiters=('\\[','\\]') if display else ('\\(','\\)')
            block=f'<{tag} class="math">{delimiters[0]}{html.escape(expression)}{delimiters[1]}</{tag}>'
            token=self.md.htmlStash.store(block)
            return '\n\n'+token+'\n\n' if display else token
        text=re.sub(r'\\\[(.*?)\\\]',lambda m:store(m,True),text,flags=re.S)
        text=re.sub(r'\$\$(.*?)\$\$',lambda m:store(m,True),text,flags=re.S)
        text=re.sub(r'\\\((.*?)\\\)',store,text,flags=re.S)
        text=re.sub(r'(?<!\\)\$(?!\s)([^$\n]+?)(?<!\s)\$',store,text)
        for i,value in enumerate(literals): text=text.replace(f'\x02LLLCODE{i}\x03',value)
        return text.split('\n')


class MathExtension(Extension):
    def extendMarkdown(self,md):
        md.preprocessors.register(MathPreprocessor(md),'lll_math',24)


def output_path(source):
    return PurePosixPath('index.html') if source=='README.md' else PurePosixPath(source).with_suffix('.html')


def site_url(source,base_path=''):
    page=output_path(source)
    return (base_path+'/' if source=='README.md' else base_path+'/'+quote(str(page),safe='/'))


def checked_path(root,name):
    path=root
    for part in PurePosixPath(name).parts:
        path=path/part
        if path.is_symlink(): raise ValueError('symlink is outside accepted website inputs: '+name)
    return path


class Links(HTMLParser):
    def __init__(self,rewrite):
        super().__init__(convert_charrefs=False)
        self.rewrite=rewrite;self.parts=[];self.ids=set();self.fragments=[]

    def tag(self,tag,attrs,closed=False):
        values=[]
        if tag=='table': self.parts.append('<div class="table-scroll" tabindex="0" role="region" aria-label="Scrollable table">')
        for key,value in attrs:
            if key=='id' and value: self.ids.add(value)
            if key in ('href','src','poster') and value: value=self.rewrite(value,tag,key,self.fragments)
            if tag=='img' and key=='src': values.append(('loading','lazy'))
            values.append((key,value))
        joined=''.join(' '+key+(f'="{html.escape(value,quote=True)}"' if value is not None else '') for key,value in values)
        self.parts.append('<'+tag+joined+(' />' if closed else '>'))

    def handle_starttag(self,tag,attrs): self.tag(tag,attrs)
    def handle_startendtag(self,tag,attrs): self.tag(tag,attrs,True)
    def handle_endtag(self,tag):
        self.parts.append('</'+tag+'>')
        if tag=='table': self.parts.append('</div>')
    def handle_data(self,data): self.parts.append(data)
    def handle_entityref(self,name): self.parts.append('&'+name+';')
    def handle_charref(self,name): self.parts.append('&#'+name+';')
    def handle_comment(self,data): self.parts.append('<!--'+data+'-->')


def local_target(source,url):
    parsed=urlsplit(url)
    if parsed.scheme or parsed.netloc:
        prefixes=(REPOSITORY+'/blob/main/', 'https://raw.githubusercontent.com/sweisman/local-level-lab/main/')
        prefix=next((p for p in prefixes if url.startswith(p)),None)
        if prefix is None: return None
        parsed=urlsplit(url[len(prefix):]);name=unquote(parsed.path)
    elif not parsed.path:
        return source,parsed
    else:
        name=unquote(parsed.path)
        name=name.lstrip('/') if name.startswith('/') else posixpath.join(posixpath.dirname(source),name)
    name=posixpath.normpath(name)
    if name=='..' or name.startswith('../') or '\\' in name:
        raise ValueError('linked path is outside repository: '+url)
    return name,parsed


def public_page(name):
    return name.endswith('.md') and PurePosixPath(name).name not in ('AGENTS.md','CLAUDE.md')


def build(root,output,*,assets,base_path='',navigation=True):
    root=Path(root).resolve();output=Path(output)
    if output.exists(): raise ValueError('website output must be a fresh directory')
    base_path='/'+base_path.strip('/') if base_path.strip('/') else ''
    queue=['README.md'];rendered={};image_paths=set();missing_pages=set();fragments=[]
    if navigation: queue.extend(name for _,name in NAVIGATION)
    sources={}
    while queue:
        source=queue.pop(0)
        if source in rendered: continue
        path=checked_path(root,source)
        if not path.is_file(): raise ValueError('required website page is missing: '+source)
        data=path.read_bytes();sources[source]=hashlib.sha256(data).hexdigest()
        content=data.decode('utf-8')
        md=markdown.Markdown(extensions=['tables','fenced_code','toc','sane_lists',MathExtension()],
                             extension_configs={'toc':{'slugify':slug}},output_format='html')
        body=md.convert(content)
        def rewrite(url,tag,key,refs):
            target=local_target(source,url)
            if target is None: return url
            name,parsed=target
            if public_page(name):
                page=checked_path(root,name)
                if page.is_file():
                    if name not in rendered and name not in queue and name!=source: queue.append(name)
                    if parsed.fragment: refs.append(dict(source=source,target=name,fragment=unquote(parsed.fragment)))
                    return urlunsplit(('', '',site_url(name,base_path),parsed.query,parsed.fragment))
                missing_pages.add(name)
            if tag=='img' and key=='src' and PurePosixPath(name).suffix.lower() in IMAGES:
                image=checked_path(root,name)
                if not image.is_file(): raise ValueError('linked image is missing: '+name)
                image_paths.add(name)
                return urlunsplit(('', '',base_path+'/'+quote(name,safe='/'),parsed.query,parsed.fragment))
            # All data, source files and directory links stay in the repository.
            kind='tree' if parsed.path.endswith('/') else 'blob'
            link=REPOSITORY+'/'+kind+'/main/'+quote(name,safe='/')
            if kind=='tree': link+='/'
            return urlunsplit(('https','github.com',urlsplit(link).path,parsed.query,parsed.fragment))
        parser=Links(rewrite);parser.feed(body);parser.close();fragments.extend(parser.fragments)
        heading=re.search(r'<h1[^>]*>(.*?)</h1>',body,flags=re.S)
        title=html.unescape(re.sub('<[^>]+>','',heading[1])) if heading else PurePosixPath(source).stem
        rendered[source]=dict(body=''.join(parser.parts),ids=parser.ids,title=title)
    missing_fragments=[r for r in fragments if r['fragment'] not in rendered[r['target']]['ids']]
    output.mkdir(parents=True)
    shutil.copytree(assets,output/'assets')
    for source,page in rendered.items():
        nav=''.join(f'<a href="{site_url(name,base_path)}"'+(' aria-current="page"' if name==source else '')+'>'+html.escape(label)+'</a>' for label,name in NAVIGATION) if navigation else ''
        canonical=DOMAIN+site_url(source)
        source_url=REPOSITORY+'/blob/main/'+quote(source,safe='/')
        template=f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(page['title'])} — Local Level Lab</title>
<meta name="description" content="Open analysis of NASA airborne IMU recordings and a stationary crowdsourced rotation-field experiment.">
<link rel="canonical" href="{canonical}"><link rel="stylesheet" href="{base_path}/assets/site.css">
<script defer src="{base_path}/assets/site.js"></script></head>
<body><a class="skip" href="#main">Skip to content</a>
<header><div class="header-inner"><a class="brand" href="{base_path}/">Local Level Lab</a>
<p class="tagline">Airborne measurements. Open methods.</p><nav aria-label="Main navigation">{nav}<a href="{REPOSITORY}">GitHub ↗</a></nav></div></header>
<main id="main"><article>{page['body']}</article></main>
<footer><a href="{source_url}">View this page on GitHub</a><span>An <a href="https://arsastronomica.com">Ars Astronomica</a> project</span></footer>
</body></html>'''
        destination=output/output_path(source);destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(template)
    for name in image_paths:
        destination=output/name;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(checked_path(root,name),destination)
    (output/'.nojekyll').write_text('')
    (output/'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: '+DOMAIN+'/sitemap.xml\n')
    sitemap='<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sitemap+=''.join('<url><loc>'+html.escape(DOMAIN+site_url(s))+'</loc></url>\n' for s in sorted(rendered))+'</urlset>\n'
    (output/'sitemap.xml').write_text(sitemap)
    not_found='<!doctype html><html lang="en"><meta charset="utf-8"><title>Page not found</title><h1>Page not found</h1><p><a href="'+base_path+'/">Return to Local Level Lab</a></p></html>'
    (output/'404.html').write_text(not_found)
    report=dict(page_count=len(rendered),image_count=len(image_paths),missing_pages=sorted(missing_pages),
                missing_fragments=missing_fragments,sources=sources,base_path=base_path,
                site_bytes=sum(p.stat().st_size for p in output.rglob('*') if p.is_file()))
    (output/'build-report.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--base-path',default='')
    args=parser.parse_args()
    report=build(HERE.parent,args.output,assets=HERE/'assets',base_path=args.base_path)
    print(json.dumps({k:v for k,v in report.items() if k!='sources'},indent=2))


if __name__=='__main__': main()
