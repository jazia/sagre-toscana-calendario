# Eventi in Toscana

Calendario iCalendar non ufficiale a cura di jazia, basato sui dati pratici di [SagreToscane.com](https://www.sagretoscane.com/cerca?category=&date=&area=&q=). Non affiliato al sito; articoli e immagini non sono ripubblicati.

## Abbonamento

In Stupid Calendar: **Impostazioni → I miei calendari → Calendari in abbonamento → Aggiungi abbonamento**. L'indirizzo rimane sempre:

https://raw.githubusercontent.com/jazia/sagre-toscana-calendario/main/eventi_toscana.ics

Usare un abbonamento tramite URL per ricevere aggiornamenti: importare un file scaricato crea una copia. Stupid Calendar controlla gli abbonamenti ogni 15 minuti mentre è aperto.

## Aggiornamento automatico

GitHub Actions esegue il controllo ogni giorno alle **05:23 UTC** (07:23 in Italia con ora legale, 06:23 con ora solare), anche a PC spento. GitHub può avviare il processo con ritardo: non è una scadenza garantita al minuto. È disponibile anche **Actions → Aggiorna calendario Toscana → Run workflow**.

Il controllo scopre il numero corrente di pagine, legge le schede, confronta le impronte dei contenuti e aggiorna il file solo dopo il completamento e la validazione. [stato.json](stato.json) riporta l'ultimo controllo riuscito; [EVENTI.md](EVENTI.md) elenca il calendario pubblicato; [DA_VERIFICARE.md](DA_VERIFICARE.md) raccoglie i casi ambigui.

- Le correzioni dell'edizione iniziale (115 manifestazioni, 191 appuntamenti) restano finché la relativa scheda non cambia.
- I nuovi eventi con date esplicite interpretabili entrano automaticamente. Weekend e domeniche separate non diventano intervalli continui.
- Programmi poco chiari, nuove date disponibili solo su immagini o modifiche alle schede con correzioni manuali richiedono revisione: i nuovi eventi incerti non sono pubblicati, per quelli esistenti resta l'ultima versione verificata. Le immagini non vengono interpretate automaticamente.
- Un annullamento esplicito nella scheda di un evento già pubblicato viene segnalato con `STATUS:CANCELLED`. La semplice scomparsa dai risultati **non** equivale ad annullamento: gli eventi futuri mancanti vengono segnalati per verifica e conservati. Gli appuntamenti passati restano nello storico.
- Errori di rete, cambiamenti incompatibili nella struttura del sito, elenchi vuoti o dati non validi fanno fallire l'esecuzione e lasciano online l'ultimo calendario valido.
- Il file di stato documenta ogni esecuzione riuscita; un controllo fallito è visibile nella sezione Actions. Il controllo automatico non sostituisce la conferma dell'organizzatore.

Le date sono di giornata intera e **non indicano apertura per 24 ore**. Consultare sempre il link della scheda per orari, prenotazioni e variazioni. Non vengono inventate ricorrenze future, né aggiunte come certe le date alternative per maltempo.

## Correzioni iniziali

- Festa del Marrone a San Piero a Sieve: 4, 11 e 18 ottobre 2026, confermati dalla locandina; il testo riportava erroneamente 19.
- La Castagna in Festa ad Arcidosso: 16–18 e 23–25 ottobre 2026, correggendo il refuso «167».
- Corona Summer: singoli appuntamenti della locandina 2026. Per il 16 agosto è mantenuta la data numerica, dato che il giorno della settimana stampato è discordante.

I collegamenti alle locandine sono nelle rispettive voci di `eventi.json` e nell'ICS. Le date di questa edizione sono state verificate il 4 ottobre 2026.

## Manutenzione

Python 3.13 e le dipendenze fissate in `requirements.txt`:

```sh
python -m pip install -r requirements.txt
python -m unittest -v
python aggiorna.py
```

`genera_calendario.py` rigenera solo dai dati locali; `aggiorna.py` legge il sito. Gli UID sono deterministici (URL della scheda + data iniziale); eventi invariati mantengono UID e DTSTAMP, mentre una data spostata sostituisce il vecchio appuntamento nel feed. `stato.json` registra i controlli senza cambiare inutilmente le date di modifica dei singoli eventi.

Per risolvere un caso manualmente, correggere periodi, note e luoghi in `eventi.json` dopo aver verificato la fonte e aggiornare `source_hash` usando `details()` sulla nuova scheda e `modified_at` in UTC. Non attribuire a una nuova edizione una vecchia correzione senza verifica.

Il workflow usa esclusivamente il token temporaneo GitHub del repository con permesso di scrittura dei contenuti, senza credenziali personali. Vengono pubblicati solo i cinque file dati indicati nel workflow; nessuna esecuzione di contenuti scaricati. GitHub Actions su esecutori standard è gratuito nei repository pubblici. I workflow pianificati possono essere disattivati da GitHub dopo 60 giorni senza attività nel repository: verificare la data dell'ultimo controllo.
