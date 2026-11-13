#!/usr/bin/env python3
"""Read-only live observations for configured Zotero and author publication lists.

No credentials, identities, site URLs, uploads or publication actions are embedded.
The website adapter understands the existing ASP author-list table structure.
"""
from __future__ import annotations
import json
import re
import tempfile
import os
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, quote
from urllib.request import Request, urlopen


def observation(status, detail, source, **extra):
    return dict(status=status, detail=detail, source=source,
                checked_at=datetime.now(timezone.utc).isoformat(), **extra)


def persist(root, doc, platform, result):
    identity = str(doc.get('paper_id') or doc.get('baseline_id') or '')
    if not identity or Path(identity).name != identity or identity in {'.', '..'}:
        return result
    path = Path(root) / 'knowledge/status_reports' / identity / (platform + '.json')
    path.parent.mkdir(parents=True, exist_ok=True)
    result['evidence_ref'] = path.relative_to(root).as_posix()
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write('\n')
        tmp = f.name
    os.replace(tmp, path)
    return result


class Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
    def handle_data(self, data):
        self.parts.append(data)


def plain(html):
    parser = Text()
    parser.feed(html)
    return ' '.join(parser.parts)


def normalized(text):
    return re.sub(r'[\s\u200b\ufeff*_#`]+', '', text).casefold()


def doi(value):
    return str(value or '').strip().casefold().removeprefix('https://doi.org/').removeprefix('http://doi.org/')


def publication_entries(html, final_url):
    entries = []
    parts = re.split(r'<tr\s+bgcolor=[\"\x27]#00FFFF[\"\x27][^>]*>', html, flags=re.I)[1:]
    for part in parts:
        body = plain(part)
        published = re.search(r'(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)', body)
        links = re.findall(r'href=[\"\x27]([^\"\x27]+)', part, re.I)
        comment = re.search(r'<td[^>]*>\s*评论[:：]?\s*</td>.*?<td[^>]*>(.*?)</td>', part, re.S)
        fields={}
        labels={'Original Abstract':'Abstract','摘要译文':'摘要翻译','评论':'评论'}
        for name,label in labels.items():
            found=re.search(r'<td[^>]*>\s*'+label+r'[:：]?\s*</td>\s*<td[^>]*>(.*?)</td>',part,re.S|re.I)
            if found: fields[name]=plain(found.group(1))
        centered=re.findall(r'<td[^>]*align=["\']center["\'][^>]*>(.*?)</td>',part,re.S|re.I)
        centered=[value for value in centered if plain(value).strip() and not re.fullmatch(r'\d+',plain(value).strip())]
        if len(centered)>=3:
            fields['英文题目']=plain(centered[0]); fields['中文题目']=plain(centered[1]); fields['作者']=plain(centered[2])
        journal=re.search(r'<td[^>]*>\s*<strong>(.*?)</strong>\s*(?:&nbsp;|\s)*(\d{4}-\d{1,2}-\d{1,2})',part,re.S|re.I)
        if journal:
            fields['期刊']=plain(journal.group(1)); fields['发表日期']='-'.join(f'{int(v):02d}' if i else v for i,v in enumerate(journal.group(2).split('-')))
        entries.append({'fields':fields,'entry_id': final_url + '#published=' + published.group(1) if published else None,
                        'published_at': published.group(1) if published else None,
                        'links': links, 'body': body,
                        'comment': plain(comment.group(1)) if comment else None})
    count = re.search(r'共发表了\s*(\d+)\s*条译评', plain(html))
    complete = bool(count and int(count.group(1)) == len(entries))
    return entries, complete


def probe_web(root, doc, config):
    cfg = config.get('web', config)
    source = cfg.get('source_url')
    if not source:
        return observation('UNKNOWN', '待核验：发布来源未配置', 'configuration')
    identity = doi(doc.get('doi') or doc.get('DOI'))
    if not identity:
        return observation('UNKNOWN', '待核验：缺少可精确匹配的DOI', source)
    try:
        cache=config.setdefault('_live_cache', {})
        if source not in cache:
            with urlopen(Request(source, headers={"User-Agent": "Literature-Evaluation-Skills/1.5.0"}), timeout=cfg.get('timeout', 15)) as response:
                raw = response.read()
                charset = cfg.get('charset') or response.headers.get_content_charset() or 'gb18030'
                cache[source]=(raw.decode(charset),response.geturl())
        html,final_url=cache[source]
        entries, complete = publication_entries(html, final_url)
        matches = [e for e in entries if any(doi(link) == identity or
                    urlparse(link).path.rstrip('/').casefold() == '/articles/' + identity.split('/')[-1]
                    for link in e['links'])]
        c = doc.get('outputs', {}).get('C', {})
        path = c.get('path') or c.get('local_path')
        comment = None
        c_sections={}; c_version=None
        if path and (Path(root) / path).is_file():
            content = (Path(root) / path).read_text(encoding='utf-8-sig')
            from artifact_binding import fingerprint
            c_version=fingerprint(Path(root)/path)
            c_sections={m.group(1).strip():m.group(2).strip() for m in re.finditer(r'^##\s+([^\n]+)\n(.*?)(?=^##\s|\Z)',content,re.M|re.S)}
            for alias in ['中文摘要','摘要翻译','Translated Abstract']:
                if alias in c_sections: c_sections['摘要译文']=c_sections[alias]
            found = re.search(r'^##\s+评论\s*\n(.*?)(?=^##\s|\Z)', content, re.M | re.S)
            comment = found.group(1) if found else None
        for entry in matches:
            entry['comment_equal'] = normalized(comment) == normalized(entry['comment']) if comment and entry['comment'] else None
            checks={}
            for field in ['英文题目','中文题目','作者','期刊','发表日期','Original Abstract','摘要译文','评论']:
                local=c_sections.get(field); remote=entry['fields'].get(field)
                if field=='作者':
                    norm=lambda value: re.sub(r'[;,，、]', '', normalized(value))
                else: norm=normalized
                checks[field]=norm(local)==norm(remote) if local and remote else None
            entry['field_comparisons']=checks
        distinct = {e['entry_id'] for e in matches if e['entry_id']}
        if len(distinct) > 1:
            status, detail = 'CONFLICT', '同文献存在两个不同实际发布条目；保留各条目及人工选择说明'
        elif matches and any(v is False for e in matches for v in e['field_comparisons'].values()):
            status, detail = 'CONFLICT', '已发布；正文或书目与当前C有差异，待核对人工润色说明'
        elif matches and all(v is True for v in matches[0]['field_comparisons'].values()):
            status,detail='VERIFIED','同文献发布正文、双语摘要、题名、作者、期刊及日期与当前C一致'
        elif matches:
            status, detail = 'PRESENT_UNVERIFIED', '同文献发布条目已确认；评论' + ('与当前C一致' if matches[0]['comment_equal'] is True else '尚未完成比较') + '，摘要与书目字段尚待核验'
        elif complete:
            status, detail = 'MISSING', '已枚举作者发布清单，未查见该文献（仅限此清单）'
        else:
            status, detail = 'UNKNOWN', '待核验：发布清单结构不支持或分页未完整枚举'
        previous = doc.get('platform_status', {}).get('web', {})
        result = observation(status, detail, source, final_url=final_url,
                             entries=matches, listing_complete=complete,
                             listing_count=len(entries), comparison_scope='public_C_body_and_bibliography',c_version=c_version,
                             c_path=path, manual_edit_notes=previous.get('manual_edit_notes', doc.get('manual_edit_notes', [])),
                             previous_user_confirmed_notes=previous.get('previous_user_confirmed_notes', []))
        return persist(root, doc, 'web', result)
    except Exception as exc:
        return observation('UNKNOWN', '本次待核验：' + str(exc), source)


def probe_zotero(root, doc, config):
    cfg = config.get('zotero', config)
    base = cfg.get('api_base_url', 'http://127.0.0.1:23119/api').rstrip('/')
    prefix = cfg.get('library_prefix')
    collection = cfg.get('collection_key')
    if not prefix or not collection:
        return observation('UNKNOWN', '待核验：Zotero目标文库或分类未配置', 'configuration')
    source = base + '/' + prefix.strip('/')
    identity = doi(doc.get('doi') or doc.get('DOI'))
    if not identity:
        return observation('UNKNOWN', '待核验：缺少可精确匹配的DOI', source)
    timeout = cfg.get('timeout', 8)
    def get(path):
        cache=config.setdefault('_live_cache', {})
        url=source+path
        if url not in cache:
            with urlopen(url, timeout=timeout) as response:
                cache[url]=json.load(response)
        return cache[url]
    try:
        parents = []
        offset = 0
        while True:
            batch = get('/items/top?limit=100&start=' + str(offset))
            parents.extend(x for x in batch if doi(x.get('data', {}).get('DOI')) == identity)
            if len(batch) < 100:
                break
            offset += 100
        records = []
        for parent in parents:
            key = parent['key']
            children = get('/items/' + quote(key, safe='') + '/children?limit=100')
            records.append({'key': key, 'title': parent['data'].get('title'),
                            'in_target_collection': collection in parent['data'].get('collections', []),
                            'children': [{'key': x['key'], 'version': x.get('version'),
                                          **{k: x.get('data', {}).get(k) for k in ['title', 'parentItem', 'contentType', 'filename', 'md5']}}
                                         for x in children]})
        if not parents:
            status, detail = 'MISSING', '已查询目标文库DOI，未查见父条目'
        elif len(parents) > 1:
            status, detail = 'CONFLICT', '同DOI多个父条目；须结合确认的Main附件身份选择，未自动归并'
        elif not records[0]['in_target_collection']:
            status, detail = 'CONFLICT', '父条目存在，但不在已配置目标分类'
        else:
            children=records[0]['children']
            role_notes=[]; missing=[]
            for role,prefixes in [('Main',('main article','pdf','[original]')),('A',('a-translation','a翻译','[a]')),('B',('b-deepreading','b精读','[b]'))]:
                candidates=[x for x in children if str(x.get('title') or '').casefold().startswith(prefixes)]
                pdfs=[x for x in candidates if x.get('contentType')=='application/pdf']
                if pdfs:
                    role_notes.append(role+' PDF已发现（内容/QC待验）')
                    if any(x.get('title') not in {'Main Article','A-Translation','B-DeepReading'} for x in pdfs): role_notes.append(role+'命名待迁移')
                else:
                    missing.append(role); role_notes.append(role+'未查见PDF')
                if any(x.get('contentType')=='application/vnd.openxmlformats-officedocument.wordprocessingml.document' for x in candidates): role_notes.append(role+'旧Word保留待处理')
            role_notes.append('SI适用来源及合并覆盖待核')
            status, detail = ('MISSING' if missing else 'PRESENT_UNVERIFIED'), '；'.join(role_notes)
        return persist(root, doc, 'zotero', observation(status, detail, source, parents=records,
                                                     collection_key=collection, verification_scope='metadata_only'))
    except Exception as exc:
        return observation('UNKNOWN', '本次待核验：' + str(exc), source)
