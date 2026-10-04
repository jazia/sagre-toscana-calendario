# Eventi in Toscana

Calendario iCalendar **non ufficiale**, preparato da jazia per Stupid Calendar a partire da [SagreToscane.com](https://www.sagretoscane.com/cerca?category=&date=&area=&q=).

## Abbonamento

In Stupid Calendar: **Impostazioni → I miei calendari → Calendari in abbonamento → Aggiungi abbonamento**. Incollare questo URL:

https://raw.githubusercontent.com/jazia/sagre-toscana-calendario/main/eventi_toscana.ics

Il collegamento può essere utilizzato anche nelle altre app compatibili con gli abbonamenti iCalendar. Importare il file scaricato crea invece una copia.

## Copertura

- Fotografia delle **12 pagine di ricerca al 4 ottobre 2026**: 10 schede per ciascuna delle prime 11 pagine e 5 nell'ultima, per **115 manifestazioni uniche**.
- **191 appuntamenti/periodi**: le sagre su più weekend sono separate per evitare falsi giorni di apertura; le manifestazioni consecutive mantengono un unico intervallo.
- Sono incluse anche le giornate già trascorse appartenenti alle manifestazioni elencate. Copertura complessiva: **16 maggio – 8 dicembre 2026**.
- Tutte le voci sono di giornata intera: rappresentano le date, **non orari di apertura di 24 ore**. Per orari, prenotazioni, biglietti e variazioni si rimanda alla scheda originale, collegata in ogni evento.
- Non vengono generate ricorrenze future non presenti nelle schede. Le date alternative per maltempo non sono appuntamenti confermati.
- È un'**estrazione puntuale**, senza aggiornamento automatico dal sito. L'abbonamento rilegge solo eventuali nuove versioni pubblicate in questo repository.

L'[elenco completo](EVENTI.md) permette di controllare tutte le date e i luoghi. I dati pratici revisionati sono in `eventi.json`, con la pagina di provenienza; gli articoli, le fotografie e le locandine non sono ripubblicati. Il calendario non è affiliato a SagreToscane.com.

## Verifiche e correzioni

- Controllate tutte le 115 schede di dettaglio; intervalli nelle intestazioni coerenti con l'elenco.
- Separati i fine settimana e le domeniche esplicitamente elencati nei programmi.
- **Festa del Marrone, San Piero a Sieve**: usati 4, 11 e **18** ottobre, confermati dalla [locandina 2026](https://www.sagretoscane.com/_data/upload/festa-del-marrone-e-dei-prodotti-tipici.jpg); il testo della scheda scrive erroneamente 19.
- **La Castagna in Festa, Arcidosso**: usati **16–18 e 23–25 ottobre**, confermati dalla [locandina](https://www.sagretoscane.com/_data/upload/la-castagna-in-festa.jpg), correggendo il refuso «167».
- **Corona Summer, Asciano**: estratti i singoli appuntamenti dalla [locandina 2026](https://www.sagretoscane.com/_data/upload/corona-summer.jpg), senza trasformare la stagione in un'apertura continua. Per il 16 agosto resta la data numerica: il giorno della settimana stampato è discordante.
- Per le feste patronali e le fiere articolate su più giorni, l'intervallo descrive la manifestazione complessiva; le singole attività possono avere giorni e orari differenti.

## Formato e manutenzione

UTF-8, righe CRLF ripiegate entro 75 ottetti, date `VALUE=DATE`, `DTEND` esclusivo, UID univoci deterministici, nessun allarme, disponibilità trasparente. Non serve un fuso orario per le date di giornata intera.

Per rigenerare dai dati già revisionati, con Python 3:

```sh
python genera_calendario.py
```

Lo script non scarica nuove schede: per una nuova edizione occorre ricontrollare le fonti, aggiornare `eventi.json`, data di estrazione e `DTSTAMP`, mantenendo gli UID degli appuntamenti invariati. I nomi delle manifestazioni e i dati pratici provengono dalle fonti collegate; i contenuti editoriali restano dei rispettivi titolari.
