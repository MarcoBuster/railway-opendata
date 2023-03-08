# Open data nell'ambito del trasporto pubblico ferroviario

- __Tesista__: Marco Aceti
- __Relatore__: Andrea Trentini

# Organizzazione del lavoro

Nella sezione 3 del file [Proposta tirocinio](./Proposta%20tirocinio.pdf) ho descritto a grandi linee tre fasi (non necessariamente da eseguire in ordine).

## 1. Indagine esplorativa
TODO - sopratutto per concordare formati.

## 2. Raccolta e produzione degli Open Data

Questa fase è divisa in sotto fasi.

### 2.1 Scraping grezzo

[Documentazione API Viaggiatreno](./VIAGGIATRENO.md).

In questa fase l'obiettivo è archiviare le risposte grezze dell'API di ViaggiaTreno sui treni in circolazione per poter essere elaborate nella fase successiva.
Quali dati salvare?

Per ogni treno...

- `andamentoTreno`: esempio per [REG 2627 del 08/03/2023](https://paste.studentiunimi.it/paste/lvtaHB5Z#sFyHHocv+HFT+JRiEY2+vXGJ0NZrERHylwkiPFaBH6h);
- `tratteCanvas`: esempio per [REG 2627 del 08/03/2023](https://paste.studentiunimi.it/paste/utVy3kYH#7hsBqOZk0ZTFFCjU5Q8rXbS0odxfAosDR3iHStyatDx).

In generale...

- `statistiche` dei treni circolanti al momento: [endpoint JSON](http://www.viaggiatreno.it/infomobilita/resteasy/viaggiatreno/statistiche/0).

### 2.2 Standardizzazione dei dati

TBD

## 3. Analisi dei dati raccolti

Periodo minimo dei dati da analizzare: __1 mese__.

TBD
