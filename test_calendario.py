import unittest,copy,json,tempfile
from pathlib import Path
from unittest.mock import patch
from datetime import datetime,timezone
import aggiorna as u
from genera_calendario import render,validate
class CalendarTests(unittest.TestCase):
 def test_weekends(self):
  self.assertEqual(u.periods('2026-10-03','2026-10-11',['Nei giorni 3-4 e 10-11 ottobre 2026.']),[['2026-10-03','2026-10-04'],['2026-10-10','2026-10-11']])
 def test_continuous(self):
  self.assertEqual(u.periods('2026-10-02','2026-10-04',['Da venerdì 2 a domenica 4 ottobre 2026.']),[['2026-10-02','2026-10-04']])
 def test_sundays(self):
  self.assertEqual(len(u.periods('2026-10-04','2026-10-25',['Domeniche 4, 11, 18 e 25 ottobre.'])),4)
 def test_cross_month(self):
  self.assertEqual(u.periods('2026-10-30','2026-11-01',['Dal 30 ottobre al 1 novembre 2026.']),[['2026-10-30','2026-11-01']])
 def test_ambiguous(self):
  for text in ['Domeniche 4-11-19 ottobre 2026.','Tutti i weekend di ottobre.','Rassegna dal 4 al 25 ottobre 2025.']:
   with self.assertRaises(u.Ambiguous):u.periods('2026-10-04','2026-10-25',[text])
 def test_explicit_cancellation_not_weather(self):
  self.assertTrue(u.cancelled('La sagra è stata annullata.'))
  self.assertFalse(u.cancelled('In caso di maltempo la sagra è annullata.'))
 def test_no_empty_or_duplicate_publish(self):
  with self.assertRaises(u.SourceError):u.index_page(u.soup('<html>Errore temporaneo</html>'))
  d=json.loads(Path('eventi.json').read_text(encoding='utf-8-sig'));d['events'].append(copy.deepcopy(d['events'][0]))
  with self.assertRaises(ValueError):render(d)
 def test_manual_correction_preserved_and_uncertainty_reported(self):
  d=json.loads(Path('eventi.json').read_text(encoding='utf-8-sig'));e=next(e for e in d['events'] if e.get('verification_url'));d['events']=[e]
  row={'url':e['url'],'name':e['name'],'category':e['category'],'location':'Test','province':'FI','start':e['periods'][0][0],'end':e['periods'][-1][1]}
  with patch.object(u,'details',return_value=(e['source_hash'],[],'')):
   result,pending=u.update(d,{e['url']:row},d['pages'],fetch=lambda _:None)
   self.assertEqual(result,d);self.assertFalse(pending)
  with patch.object(u,'details',return_value=('changed',[],'')),patch.object(u,'periods',return_value=e['periods']):
   result,pending=u.update(d,{e['url']:row},d['pages'],fetch=lambda _:None)
   self.assertEqual(result['events'],d['events']);self.assertEqual(len(pending),1)
 def test_future_missing_is_not_deleted(self):
  d=json.loads(Path('eventi.json').read_text(encoding='utf-8-sig'));d['events']=d['events'][:1]
  result,pending=u.update(d,{},d['pages'],now=datetime(2026,1,1,tzinfo=timezone.utc))
  self.assertEqual(result['events'],d['events']);self.assertTrue(pending)
 def test_network_failure_leaves_all_files_untouched(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);root.joinpath('eventi.json').write_text('{"events":[]}');root.joinpath('eventi_toscana.ics').write_bytes(b'previous valid version')
   with patch.object(u,'ROOT',root),patch.object(u,'listing',side_effect=u.SourceError('offline')):
    with self.assertRaises(u.SourceError):u.main()
   self.assertEqual(root.joinpath('eventi_toscana.ics').read_bytes(),b'previous valid version')
 def test_new_event_updated_event_and_cancellation(self):
  row={'url':u.BASE+'/sagre/test.html','name':'Sagra di prova','category':'Sagre','location':'Firenze','province':'FI','start':'2026-10-03','end':'2026-10-11'}
  d={'events':[],'pages':[],'extracted_at':'2026-10-04'}
  with patch.object(u,'details',return_value=('one',['Nei giorni 3-4 e 10-11 ottobre 2026.'],'')):
   result,pending=u.update(d,{row['url']:row},[],fetch=lambda _:None)
  self.assertFalse(pending);self.assertEqual(len(result['events'][0]['periods']),2)
  changed=dict(row,name='Nuovo titolo')
  with patch.object(u,'details',return_value=('two',['Nei giorni 3-4 e 10-11 ottobre 2026.'],'')):
   updated,pending=u.update(result,{row['url']:changed},[],fetch=lambda _:None)
  self.assertEqual(updated['events'][0]['name'],'Nuovo titolo')
  with patch.object(u,'details',return_value=('three',[],'La sagra è stata annullata.')):
   cancelled,pending=u.update(updated,{row['url']:changed},[],fetch=lambda _:None)
  self.assertEqual(cancelled['events'][0]['status'],'CANCELLED')
  self.assertEqual(validate(render(cancelled)[0]),2)
 def test_pagination_finds_more_than_initial_twelve(self):
  self.assertEqual(u.page_urls(u.soup('<a href="/cerca?page=17">Ultima</a>')),{17})
 def test_renderer_valid_and_uids_stable(self):
  d=json.loads(Path('eventi.json').read_text(encoding='utf-8-sig'));first,_=render(d)
  from icalendar import Calendar
  old={str(e['UID']) for e in Calendar.from_ical(Path('eventi_toscana.ics').read_bytes()).walk('VEVENT')}
  new={str(e['UID']) for e in Calendar.from_ical(first).walk('VEVENT')}
  self.assertEqual(old,new);self.assertEqual(validate(first),len(new))
if __name__=='__main__':unittest.main()
