"""Rigenera l'ICS dai dati revisionati; Python 3, nessuna dipendenza esterna."""
import json
import hashlib
from pathlib import Path
from datetime import date, timedelta
ROOT = Path(__file__).resolve().parent

def escape(value):
    return str(value).replace('\\', '\\\\').replace('\n', '\\n').replace(';', '\\;').replace(',', '\\,')

def fold(line):
    chunks=[]; current=''
    for char in line:
        if len((current+char).encode('utf-8')) > 75:
            chunks.append(current); current=' '
        current+=char
    chunks.append(current)
    return '\r\n'.join(chunks)

def generate():
    data=json.loads((ROOT/'eventi.json').read_text(encoding='utf-8'))
    lines=['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//jazia//Eventi Toscana - calendario non ufficiale//IT','CALSCALE:GREGORIAN','METHOD:PUBLISH','X-WR-CALNAME:Eventi in Toscana','X-WR-CALDESC:Estrazione del 4 ottobre 2026 da SagreToscane.com. Calendario non ufficiale.','X-WR-TIMEZONE:Europe/Rome']
    rows=['# Elenco degli appuntamenti','', 'Estrazione del 4 ottobre 2026: 115 schede dalle 12 pagine di SagreToscane.com, suddivise in 191 periodi effettivi. Le date finali in questa tabella sono inclusive.','', '| Evento | Dal | Al | Luogo |','|---|---|---|---|']
    seen=set()
    for e in data['events']:
        for i,(start,end) in enumerate(e['periods']):
            a=date.fromisoformat(start); b=date.fromisoformat(end)
            assert a<=b
            title=e['name']
            if e.get('period_titles'):title+=' — '+e['period_titles'][i]
            loc=e.get('period_locations',[e['location']]*len(e['periods']))[i]
            uid=hashlib.sha256((e['url']+'|'+start).encode()).hexdigest()[:32]+'@sagre-toscana.jazia'
            assert uid not in seen;seen.add(uid)
            desc='Fonte: SagreToscane.com\nScheda e programma: '+e['url']+'\nRilevazione: 4 ottobre 2026.\nLe date indicano i giorni della manifestazione, non un’apertura di 24 ore. Verificare orari, prenotazioni ed eventuali variazioni nella scheda originale.'
            if e['note']:desc+='\n'+e['note']
            if e.get('verification_url'):desc+='\nLocandina consultata: '+e['verification_url']
            lines+=['BEGIN:VEVENT','UID:'+uid,'DTSTAMP:20261004T180000Z','DTSTART;VALUE=DATE:'+a.strftime('%Y%m%d'),'DTEND;VALUE=DATE:'+(b+timedelta(days=1)).strftime('%Y%m%d'),'SUMMARY;LANGUAGE=it:'+escape(title),'LOCATION:'+escape(loc),'DESCRIPTION;LANGUAGE=it:'+escape(desc),'URL:'+e['url'],'CATEGORIES:'+escape(e['category']),'TRANSP:TRANSPARENT','CLASS:PUBLIC','END:VEVENT']
            rows.append(f"| [{title.replace('|','–')}]({e['url']}) | {a:%d/%m/%Y} | {b:%d/%m/%Y} | {loc} |")
    lines+=['END:VCALENDAR']
    (ROOT/'eventi_toscana.ics').write_bytes(('\r\n'.join(fold(line) for line in lines)+'\r\n').encode('utf-8'))
    (ROOT/'EVENTI.md').write_text('\n'.join(rows)+'\n',encoding='utf-8')
    print(f'{len(data["events"])} schede; {len(seen)} appuntamenti generati.')
if __name__=='__main__':generate()
