"""Aggiornamento conservativo da SagreToscane.com; dati incerti in DA_VERIFICARE.md."""
from __future__ import annotations
import copy, hashlib, json, re, time, urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parent
BASE='https://www.sagretoscane.com'
SEARCH=BASE+'/cerca?category=&date=&area=&q='
MONTHS='gennaio febbraio marzo aprile maggio giugno luglio agosto settembre ottobre novembre dicembre'.split()
DAY=r'(?<!\d)(?:[12]?\d|3[01])(?!\d)'
WEEKDAYS=r'\b(?:luned[iì]|marted[iì]|mercoled[iì]|gioved[iì]|venerd[iì]|sabato|domenica)\b'

class SourceError(RuntimeError): pass
class Ambiguous(ValueError): pass

def soup(raw): return BeautifulSoup(raw,'html.parser')
def txt(node): return ' '.join(node.get_text(' ',strip=True).split()) if node else ''
def digest(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
def get(url):
    if urlparse(url).hostname!='www.sagretoscane.com':raise SourceError('Dominio inatteso')
    for attempt in range(3):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'EventiToscanaCalendar/1.0 (+https://github.com/jazia/sagre-toscana-calendario)'})
            with urllib.request.urlopen(req,timeout=40) as response:
                if urlparse(response.url).hostname!='www.sagretoscane.com':raise SourceError('Redirect inatteso')
                body=response.read(3_000_001)
                if len(body)>3_000_000:raise SourceError('Pagina troppo grande')
            time.sleep(.3)
            return soup(body)
        except Exception:
            if attempt==2:raise
            time.sleep(2**attempt)

def bounds(node):
    a=node.select_one('[itemprop=startDate]');b=node.select_one('[itemprop=endDate]')
    if a is None:raise SourceError('Data iniziale assente')
    start=date.fromisoformat(a['datetime']);end=date.fromisoformat(b['datetime']) if b else start
    if end<start:raise SourceError('Intervallo invertito')
    return start.isoformat(),end.isoformat()

def index_page(doc):
    result=[]
    for p in doc.select('.post[itemtype="https://schema.org/Event"]'):
        try:
            start,end=bounds(p)
            row={'url':p.select_one('[itemprop=url]')['href'],'name':txt(p.select_one('[itemprop=name]')),'start':start,'end':end,
                'location':txt(p.select_one('[itemprop=location]')),'province':txt(p.select_one('.province')).upper(),'category':txt(p.select_one('.postTags'))}
            if not row['name'] or not row['location'] or urlparse(row['url']).hostname!='www.sagretoscane.com':raise ValueError()
            result.append(row)
        except Exception as exc:raise SourceError('Struttura elenco cambiata') from exc
    if not result:raise SourceError('Elenco vuoto: conservato il calendario precedente')
    return result

def page_urls(doc):
    urls=set()
    for a in doc.select('a[href]'):
        u=urljoin(BASE,a['href']);parsed=urlparse(u)
        if parsed.hostname=='www.sagretoscane.com' and parsed.path=='/cerca':
            values=parse_qs(parsed.query).get('page',[])
            if values:
                n=int(values[0])
                if n<1 or n>300:raise SourceError('Numero di pagine inatteso')
                urls.add(n)
    return urls

def listing(fetch=get):
    first=fetch(SEARCH);pages={1:first};maximum=max(page_urls(first)|{1})
    n=2
    while n<=maximum:
        doc=fetch(BASE+f'/cerca?q=&category=&tag=&area=&city=&date=&page={n}')
        pages[n]=doc;maximum=max(page_urls(doc)|{maximum});n+=1
    rows={};counts=[]
    for n,doc in pages.items():
        found=index_page(doc);counts.append({'page':n,'count':len(found)})
        for row in found:
            if row['url'] in rows:raise SourceError('Duplicati tra pagine: riprovare al prossimo controllo')
            rows[row['url']]=row
    return rows,counts

def details(row,doc):
    node=doc.select_one('.postContentDescription');heading=doc.select_one('h1');dates=doc.select_one('.postDates')
    if node is None or heading is None or dates is None:raise SourceError('Scheda incompleta')
    start,end=bounds(dates)
    if (start,end)!=(row['start'],row['end']):raise SourceError('Date cambiate durante la lettura')
    paragraphs=[txt(p) for p in node.select('p') if txt(p)]
    content=txt(node)
    images=[img.get('src','') for img in node.parent.select('img') if '/_data/upload/' in img.get('src','')]
    fingerprint=digest({'name':row['name'],'start':start,'end':end,'location':row['location'],'province':row['province'],'category':row['category'],'text':content,'images':images})
    return fingerprint,paragraphs,content

def grouped(days):
    result=[]
    for day in sorted(days):
        value=day.isoformat()
        if result and date.fromisoformat(result[-1][1])+timedelta(days=1)==day:result[-1][1]=value
        else:result.append([value,value])
    return result

def periods(start,end,paragraphs):
    a=date.fromisoformat(start);b=date.fromisoformat(end)
    intro=paragraphs[0].lower() if paragraphs else ''
    if a.year!=b.year:raise Ambiguous('Intervallo a cavallo di due anni da verificare')
    explicit_years={int(y) for y in re.findall(r'\b20\d{2}\b',intro)}
    if explicit_years and explicit_years!={a.year}:raise Ambiguous('Anno discordante nel programma')
    # Rimuove i giorni della settimana, non le date. Non interpreta locandine né orari.
    text=re.sub(WEEKDAYS,'',intro).replace('°','').replace('º','')
    text=re.sub(r"all['’]",'al ',text);text=re.sub(r'\s+',' ',text)
    days=set();spans=[]
    month_pattern='|'.join(MONTHS)
    pattern=rf'({DAY}(?:\s*(?:-|–|,|\be\b|\bal\b|\ba\b)\s*{DAY})*)\s*(?:di\s+)?({month_pattern})\b'
    for match in re.finditer(pattern,text):
        month=MONTHS.index(match[2])+1
        numbers=[int(d) for d in re.findall(r'\d+',match[1])]
        if any(d==0 for d in numbers):raise Ambiguous('Giorno non valido')
        if re.search(r'\b(?:al|a)\b',match[1]):
            if len(numbers)!=2 or numbers[0]>numbers[1]:raise Ambiguous('Intervallo non chiaro')
            numbers=list(range(numbers[0],numbers[1]+1))
        try:values=[date(a.year,month,d) for d in numbers]
        except ValueError as exc:raise Ambiguous('Data non valida') from exc
        days.update(values);spans.append((match.start(),match.end(),values))
    # Intervallo continuo esplicito tra mesi diversi, per esempio dal 26 settembre al 1 novembre.
    if len(spans)==2 and len(spans[0][2])==len(spans[1][2])==1:
        bridge=text[spans[0][1]:spans[1][0]]
        if re.fullmatch(r'\s*(?:\d{4}\s*)?(?:al|a)\s*',bridge):
            x,y=spans[0][2][0],spans[1][2][0]
            if x<=y:days={x+timedelta(days=i) for i in range((y-x).days+1)}
    if not days:
        if a==b:return [[start,end]]
        raise Ambiguous('Giorni effettivi non ricavabili con certezza dal testo')
    if min(days)!=a or max(days)!=b:raise Ambiguous('Date del programma discordanti con intestazione')
    weekend=bool(re.search(r'week\s*-?\s*end|fine settimana',intro))
    sundays=bool(re.search(r'tutte le domeniche|quattro domeniche|tre domeniche|due domeniche',intro))
    if weekend and len(days)>4 and days=={a+timedelta(days=i) for i in range((b-a).days+1)}:
        # Solo "ogni sabato e domenica" o "tutti i weekend" è una regola abbastanza esplicita.
        if re.search(r'ogni sabato e domenica|tutti i (?:weekend|fine settimana)',intro):days={d for d in days if d.weekday()>=5}
        else:raise Ambiguous('Weekend non enumerati chiaramente')
    if sundays and any(d.weekday()!=6 for d in days):raise Ambiguous('Domeniche discordanti')
    if (b-a).days>31:raise Ambiguous('Rassegna lunga: serve controllo del programma')
    return grouped(days)

def cancelled(content):
    return bool(re.search(r'(?:evento|manifestazione|sagra|festa)\s+(?:è\s+)?(?:stat[ao]\s+)?annullat[ao]\b',content,re.I)) and not bool(re.search(r'in caso.{0,80}annullat',content,re.I))

def update(data,rows,counts,fetch=get,now=None):
    now=now or datetime.now(timezone.utc);stamp=now.strftime('%Y%m%dT%H%M%SZ');today=now.date().isoformat()
    output=copy.deepcopy(data);old={e['url']:e for e in output['events']};pending=[]
    for url,row in rows.items():
        fingerprint,paragraphs,content=details(row,fetch(url));existing=old.get(url)
        if existing and existing.get('source_hash')==fingerprint:continue
        if existing and cancelled(content):
            existing.update(status='CANCELLED',source_hash=fingerprint,modified_at=stamp);continue
        if cancelled(content):continue
        try:new_periods=periods(row['start'],row['end'],paragraphs)
        except Ambiguous as exc:
            pending.append({'url':url,'name':row['name'],'reason':str(exc)})
            continue
        # Una locandina o le annotazioni personalizzate richiedono revisione se la scheda cambia.
        if existing and (existing.get('verification_url') or existing.get('period_titles') or existing.get('period_locations')):
            pending.append({'url':url,'name':row['name'],'reason':'Scheda già revisionata manualmente modificata: ricontrollare le correzioni'})
            continue
        if existing:
            # Se cambia l'edizione non trascina vecchio luogo e vecchie note in quella nuova.
            same_edition=existing['periods'][0][0][:4]==row['start'][:4]
            replacement=copy.deepcopy(existing) if same_edition else {}
        else:replacement={}
        replacement.update(name=row['name'],url=url,category=row['category'],periods=new_periods,source_hash=fingerprint,modified_at=stamp,status='CONFIRMED')
        replacement.setdefault('location',f"{row['location']} ({row['province']}), Toscana, Italia")
        replacement.setdefault('note','')
        # URL+data mantiene gli UID precedenti; una nuova data ottiene un nuovo UID.
        old[url]=replacement
    for url,event in old.items():
        if url not in rows and event['periods'][-1][1]>=today:
            pending.append({'url':url,'name':event['name'],'reason':'Evento futuro non più nell’elenco: conservato, assenza non equivale ad annullamento'})
    output['events']=sorted(old.values(),key=lambda e:(e['periods'][0][0],e['url']))
    output['pages']=counts
    if output!=data:
        output['extracted_at']=today;output['updated_at']=stamp
    return output,pending

def main():
    data=json.loads((ROOT/'eventi.json').read_text(encoding='utf-8-sig'))
    rows,counts=listing();result,pending=update(data,rows,counts)
    # Nessun file pubblicabile viene modificato prima del completamento di tutti i download.
    from genera_calendario import render,validate
    ics,table=render(result);validate(ics)
    (ROOT/'eventi.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (ROOT/'eventi_toscana.ics').write_bytes(ics)
    (ROOT/'EVENTI.md').write_text(table,encoding='utf-8')
    report=['# Eventi da verificare','', 'Le schede ambigue nuove non entrano nel feed; per quelle già pubblicate resta l’ultima versione verificata.','']
    report.extend(f"- [{p['name']}]({p['url']}): {p['reason']}." for p in pending)
    if not pending:report.append('Nessuna revisione richiesta.')
    (ROOT/'DA_VERIFICARE.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
    status={'last_success_utc':datetime.now(timezone.utc).isoformat(),'pages':len(counts),'source_events':len(rows),'published_events':len(result['events']),'review_needed':len(pending)}
    (ROOT/'stato.json').write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(status))
    if pending:print(f'::warning::{len(pending)} schede richiedono controllo: vedere DA_VERIFICARE.md')
if __name__=='__main__':main()
