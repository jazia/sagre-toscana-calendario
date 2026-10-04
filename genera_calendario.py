"""Genera e valida il calendario dai dati revisionati."""
import json,hashlib
from pathlib import Path
from datetime import date,timedelta
from icalendar import Calendar
ROOT=Path(__file__).resolve().parent

def escape(value):return str(value).replace('\\','\\\\').replace('\n','\\n').replace(';','\\;').replace(',','\\,')
def fold(line):
    chunks=[];current=''
    for char in line:
        if len((current+char).encode('utf-8'))>75:chunks.append(current);current=' '
        current+=char
    return '\r\n'.join(chunks+[current])
def render(data):
    updated=data.get('updated_at','20261004T180000Z');day=data['extracted_at']
    count=sum(len(e['periods']) for e in data['events'])
    lines=['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//jazia//Eventi Toscana - calendario non ufficiale//IT','CALSCALE:GREGORIAN','METHOD:PUBLISH','X-WR-CALNAME:Eventi in Toscana','X-WR-CALDESC:'+escape(f'Ultima modifica dati: {day}. Fonte: SagreToscane.com. Calendario non ufficiale.'),'X-WR-TIMEZONE:Europe/Rome']
    rows=['# Elenco degli appuntamenti','',f'Ultima modifica dati: {day}. {len(data["events"])} manifestazioni, {count} appuntamenti/periodi. Date finali inclusive. Il controllo giornaliero è registrato in [stato.json](stato.json); le incertezze in [DA_VERIFICARE.md](DA_VERIFICARE.md).','', '| Evento | Dal | Al | Luogo | Stato |','|---|---|---|---|---|']
    seen=set()
    for e in data['events']:
        for i,(start,end) in enumerate(e['periods']):
            a=date.fromisoformat(start);b=date.fromisoformat(end)
            if a>b:raise ValueError('Intervallo invertito')
            title=e['name']
            if e.get('period_titles'):title+=' — '+e['period_titles'][i]
            loc=e.get('period_locations',[e['location']]*len(e['periods']))[i]
            uid=hashlib.sha256((e['url']+'|'+start).encode()).hexdigest()[:32]+'@sagre-toscana.jazia'
            if uid in seen:raise ValueError('UID duplicato')
            seen.add(uid)
            desc='Fonte: SagreToscane.com\nScheda e programma: '+e['url']+'\nLe date indicano i giorni della manifestazione, non un’apertura di 24 ore. Verificare orari, prenotazioni ed eventuali variazioni nella scheda originale.'
            if e.get('note'):desc+='\n'+e['note']
            if e.get('verification_url'):desc+='\nLocandina consultata: '+e['verification_url']
            state=e.get('status','CONFIRMED')
            lines+=['BEGIN:VEVENT','UID:'+uid,'DTSTAMP:'+e.get('modified_at','20261004T180000Z'),'DTSTART;VALUE=DATE:'+a.strftime('%Y%m%d'),'DTEND;VALUE=DATE:'+(b+timedelta(days=1)).strftime('%Y%m%d'),'SUMMARY;LANGUAGE=it:'+escape(title),'LOCATION:'+escape(loc),'DESCRIPTION;LANGUAGE=it:'+escape(desc),'URL:'+e['url'],'CATEGORIES:'+escape(e['category']),'STATUS:'+state,'TRANSP:TRANSPARENT','CLASS:PUBLIC','END:VEVENT']
            safe_title=title.replace('|','–').replace('[','(').replace(']',')')
            rows.append(f"| [{safe_title}]({e['url']}) | {a:%d/%m/%Y} | {b:%d/%m/%Y} | {loc.replace('|','–')} | {'Annullato' if state=='CANCELLED' else ''} |")
    lines+=['END:VCALENDAR']
    return ('\r\n'.join(fold(line) for line in lines)+'\r\n').encode('utf-8'),'\n'.join(rows)+'\n'
def validate(raw):
    if b'\n' in raw.replace(b'\r\n',b'') or any(len(l)>75 for l in raw.split(b'\r\n')):raise ValueError('Formato ICS errato')
    events=Calendar.from_ical(raw).walk('VEVENT');seen=set()
    if not events:raise ValueError('Il calendario vuoto non viene pubblicato')
    for e in events:
        uid=str(e['UID'])
        if e.errors or uid in seen or type(e.decoded('DTSTART')) is not date or e.decoded('DTEND')<=e.decoded('DTSTART'):raise ValueError('Evento non valido')
        seen.add(uid)
    return len(events)
def generate():
    raw,table=render(json.loads((ROOT/'eventi.json').read_text(encoding='utf-8-sig')));print('Eventi validati:',validate(raw))
    (ROOT/'eventi_toscana.ics').write_bytes(raw);(ROOT/'EVENTI.md').write_text(table,encoding='utf-8')
if __name__=='__main__':generate()
