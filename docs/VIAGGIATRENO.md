# API di Viaggiatreno

## Link utili

- [+++TRENITALIA SHOCK+++ NON crederete MAI a queste API \*painful\*](https://medium.com/@albigiu/trenitalia-shock-non-crederete-mai-a-queste-api-painful-14433096502c) (era obbligatorio metterlo);
- [GitHub sabas/trenitalia](https://github.com/sabas/trenitalia): sono documentate parzialmente le **richieste** di alcuni metodi ma non le risposte;
- [GitHub Razorphyn/Informazioni-Treni-Italiani](https://github.com/Razorphyn/Informazioni-Treni-Italiani): sono parzialmente documentate le **risposte** di alcuni metodi ed è presente un file [`ID_STAZIONI.csv`](https://github.com/Razorphyn/Informazioni-Treni-Italiani/blob/master/ID_STAZIONI.csv), ma è sicuramente _out-of-date_ in quanto è stato generato almeno 9 anni fa;
- [GitHub roughconsensusandrunningcode/TrainMonitor (wiki)](https://github.com/roughconsensusandrunningcode/TrainMonitor/wiki/API-del-sistema-Viaggiatreno): è documentata bene la risposta di alcuni metodi, in particolare __`andamentoTreno`__.
Nella repo sono presenti degli script per dumpare le stazioni;

## Definizioni e caveats

- Una __stazione__ è un _luogo di sosta temporanea_ per i convogli ferroviari.
- Un __treno__ è la corsa di un _convoglio ferroviario_ in una giornata.
    - È __identificato univocamente__ dalla tripla $(\text{Data}, \, \text{StazioneDiPartenza}, \, \text{NumeroDiTreno})$.
    In nessun caso il $\text{NumeroDiTreno}$ può essere utilizzato come identificatore univoco.
- Una __fermata__ è una stazione in cui un treno, oltre che a transitare, _sosta_.
    - Un treno sosta in __almeno due__ fermate.
    - Per ogni fermata di un treno sono associate alcune informazioni, come:
        - _tipo fermata_ (ordinaria, straordinaria, soppressa, ...);
        - orario _programmato_ ed _effettivo_ di arrivo;
        - orario _programmato_ ed _effettivo_ di partenza;
        - binario _programmato_ ed _effettivo_ di arrivo;
        - binario _programmato_ ed _effettivo di partenza_;
            - Secondo la struttura delle API di ViaggiaTreno, un treno potrebbe arrivare in una stazione da un binario e partire da un altro.
            Ritengo ragionevole assumere che i binari di arrivo e partenza di un treno dalla stessa fermata siano sempre gli stessi.
    - La _prima_ e l'_ultima_ fermata sono fermate particolari denominate _origine_ e _destinazione_ e hanno rispettivamente orari di arrivi e partenza nulli.
- In questo documento, tutti i __timestamp__ sono intesi a precisione di millisecondi (multipli di 1000).

# Metodi

> __Endpoint base__: `http://www.viaggiatreno.it/infomobilita/resteasy/viaggiatreno/<metodo>/[parametro1]/.../[parametroN]`

## `/cercaNumeroTrenoTrenoAutocomplete/<numeroTreno>`

Il metodo serve per disambugare treni con lo stesso numero ma aventi origini differenti.

### Parametri
- `numeroTreno`: il numero di treno richiesto.

### Risposta

Formato proprietario.

```
numeroTreno - nomeStazioneOrigine1|numeroTreno-codiceStazioneOrigine1-timestampMezzanotteOggi
...
numeroTreno - nomeStazioneOrigineN|numeroTreno-codiceStazioneOrigineN-timestampMezzanotteOggi
```

### Esempio
> [/cercaNumeroTrenoTrenoAutocomplete/2107](http://www.viaggiatreno.it/infomobilita/resteasy/viaggiatreno/cercaNumeroTrenoTrenoAutocomplete/2107)
> ```
> 2107 - TORINO PORTA NUOVA|2107-S00219-1678230000000
> 2107 - MILANO NORD CADORNA|2107-N00001-1678230000000
> ```

## `/cercaStazione/<stringa>`

Controintuitivamente, il metodo ritorna non una bensì tutte le stazioni cui nome inizia con `stringa`.

### Parametri
- `stringa`: query di ricerca &mdash; __può essere lunga anche un solo carattere__.

### Risposta

Formato JSON.

```json
[
  {
    "nomeLungo": "MILANO CENTRALE", // nome lungo
    "nomeBreve": "Milano Centrale", // nome breve?
    "label": "Milano",              // può essere nullo, indica la città?
    "id": "S01700"                  // ID stazione
  },
  // ...
]
```

### Caveats

- Il metodo __non restituisce tutte le stazioni__. \
Per esempio, la [stazione di Arcene](https://it.wikipedia.org/wiki/Stazione_di_Arcene) (ID S01608) non è mai ritornata dalla ricerca (nemmeno dal sito web ufficiale): il suo ID è reperibile solo visualizzando le fermate di un treno in corsa.

### Esempio
> [/cercaStazione/MILANO P](http://www.viaggiatreno.it/infomobilita/resteasy/viaggiatreno/cercaStazione/MILANO%20P)
> ```json
> [
>  {
>    "nomeLungo": "MILANO PORTA GARIBALDI",
>    "nomeBreve": "MI P. Garibaldi",
>    "label": null,
>    "id": "S01645"
>  },
>  {
>    "nomeLungo": "MILANO PORTA ROMANA",
>    "nomeBreve": "MI P.ta Romana",
>    "label": null,
>    "id": "S01632"
>  },
>  {
>    "nomeLungo": "MILANO PORTA VITTORIA",
>    "nomeBreve": "MI P.ta Vittoria",
>    "label": null,
>    "id": "S01633"
>  }
>]
> ```

Ulteriori caveats:
- assenza della stazione di _Milano Porta Romana_, chiamata nel loro database solo con _Milano Romana_;
- inconsistenza dei _nomi brevi_ rispetto ai _nomi lunghi_ (per indicare _porta_, talvolta P. altre volte P.ta).

## `/regione/<IDStazione>`

Trova il codice della regione di appartenenza di una stazione.
Utile per i metodi successivi.

### Parametri
- `IDStazione`: l'ID della stazione in formato inalterato.

### Risposta
Codice della regione di appartenenza della stazione.

Una lista esaustiva dei codici è reperibile nella [repo di Razorphyn](https://github.com/Razorphyn/Informazioni-Treni-Italiani/blob/master/ID_REGIONI.csv).

### Caveats
- Il server imposta l'header `Content-Type` a `application/json`, ma il risultato non è JSON;
- I codici 21 e 22 fanno entrambi riferimento al Trentino-Alto Adige.
- Per alcuni stazioni (come AIELLO, S08550) la richiesta ritorna HTTP 204.
In tal caso, non c'è modo di reperire dettagli ulteriori della stazione.

### Esempio
> [/regione/S01700](http://www.viaggiatreno.it/infomobilita/resteasy/viaggiatreno/regione/S01700)
> ```
> 1
> ```

## `/elencoStazioni/<codiceRegione>`

### Parametri
- `codiceRegione`: fare riferimento a [repo di Razorphyn](https://github.com/Razorphyn/Informazioni-Treni-Italiani/blob/master/ID_REGIONI.csv). \
Il codice `0` sembra ritornare le stazioni principali italiane.

### Risposta

Formato JSON.

```json
[
 {
    "codReg": 3,    // codice regione nella richiesta ?
    "tipoStazione": 3,
    "dettZoomStaz": [
      {
        "codiceStazione": "S01013",
        "zoomStartRange": 8,
        "zoomStopRange": 9,
        "pinpointVisibile": true,
        "pinpointVisible": true,
        "labelVisibile": true,
        "labelVisible": true,
        "codiceRegione": null
      },
      {
        "codiceStazione": "S01013",
        "zoomStartRange": 10,
        "zoomStopRange": 11,
        "pinpointVisibile": true,
        "pinpointVisible": true,
        "labelVisibile": true,
        "labelVisible": true,
        "codiceRegione": null
      }
    ],
    "pstaz": [],
    "mappaCitta": {
      "urlImagePinpoint": "",
      "urlImageBaloon": ""
    },
    "codiceStazione": "S01013",
    "codStazione": "S01013",
    "lat": 45.943821,   // latitudine
    "lon": 8.47224,     // longitudine
    "latMappaCitta": 0,
    "lonMappaCitta": 0,
    "localita": {
      "nomeLungo": "VERBANIA-PALLANZA",
      "nomeBreve": "Verbania",
      "label": "Verbania-Pallanza",
      "id": "S01013"
    },
    "esterno": false,
    "offsetX": -4,
    "offsetY": 10,
    "nomeCitta": "Verbania"
  },
  // ...
]
```

Alcuni tentativi di documentazione dei campi (da _trial-and-error_):
- `tipoStazione`:
    - `3`: regolare;
    - `1`: stazione principale (?);
    - `4`: placeholder, da ignorare.
- `localita` contiene le stesse info del JSON restituito da `cercaStazione`;
- l'intuito porta a pensare che `codiceStazione`, `codStazione` e `localita.id` siano sempre uguali: non sono stati ancora trovati controesempi.

### Caveats

- `nomeCitta` può essere nullo o `"A"` (stesso significato);
- rispetto al metodo `cercaStazione` __più stazioni__ sono presenti, ma comunque __non tutte__.
In particolare, le stazioni senza informazioni aggiuntive (come AIELLO, S08550) non sono visualizzate _in toto_.
- alcune stazioni possono essere __in più regioni contemporaneamente__: per esempio, la stazione di CASALMAGGIORE (S01850) viene ritornata dall'elenco della Lombardia (1) e da quello dell'Emilia Romagna (8).
Utilizzando il metodo `/regione`, però, è chiaro come la regione si trovi in realtà in Lombardia.

### Esempio

> [/elencoStazioni/1](http://www.viaggiatreno.it/infomobilita/resteasy/viaggiatreno/elencoStazioni/1) (Lombardia)
> ```
> (omissis)
> ```

## `/partenze/<IDStazione>/<orarioAttuale>`

Ritorna l'elenco dei treni in partenza nella stazione e nell'orario dato.

### Parametri

- `IDStazione`: l'ID della stazione in formato inalterato;
- `orarioAttuale`: l'orario di riferimento.
Orari diversi da quello attuale possono portare a risultati parziali o errori.
Per questo campo, il __formato è tremendo e demenziale__ per un API:
```
%a %b %d %Y %H:%M:%S %Z%z
```

### Risposta

Un array JSON.

```json
[
  {
    "numeroTreno": 9584,
    "categoria": "",
    "categoriaDescrizione": " FR",
    "origine": null,
    "codOrigine": "S11781",
    "destinazione": "TORINO P.NUOVA",
    "codDestinazione": null,
    "origineEstera": null,
    "destinazioneEstera": null,
    "oraPartenzaEstera": null,
    "oraArrivoEstera": null,
    "tratta": 0,
    "regione": 0,
    "origineZero": null,
    "destinazioneZero": null,
    "orarioPartenzaZero": null,
    "orarioArrivoZero": null,
    "circolante": true,
    "codiceCliente": 1,
    "binarioEffettivoArrivoCodice": null,
    "binarioEffettivoArrivoDescrizione": null,
    "binarioEffettivoArrivoTipo": null,
    "binarioProgrammatoArrivoCodice": null,
    "binarioProgrammatoArrivoDescrizione": null,
    "binarioEffettivoPartenzaCodice": null,
    "binarioEffettivoPartenzaDescrizione": null,
    "binarioEffettivoPartenzaTipo": null,
    "binarioProgrammatoPartenzaCodice": null,
    "binarioProgrammatoPartenzaDescrizione": "12",
    "subTitle": null,
    "esisteCorsaZero": null,
    "orientamento": "B",
    "inStazione": false,
    "haCambiNumero": false,
    "nonPartito": false,
    "provvedimento": 0,
    "riprogrammazione": "N",
    "orarioPartenza": 1678291320000,
    "orarioArrivo": null,
    "stazionePartenza": null,
    "stazioneArrivo": null,
    "statoTreno": null,
    "corrispondenze": null,
    "servizi": null,
    "ritardo": 23,
    "tipoProdotto": "100",
    "compOrarioPartenzaZeroEffettivo": "17:02",
    "compOrarioArrivoZeroEffettivo": null,
    "compOrarioPartenzaZero": "17:02",
    "compOrarioArrivoZero": null,
    "compOrarioArrivo": null,
    "compOrarioPartenza": "17:02",
    "compNumeroTreno": " FR 9584",
    "compOrientamento": [
      "Executive in testa",
      "Executive in the head",
      "Executive Zugspitze",
      "Executive en t&ecirc;te",
      "Executive al inicio del tren",
      "Executive la &icirc;nceputul trenului",
      "頭の中でExecutive",
      "Executive在前几节车厢",
      "Executive в головной части поезда"
    ],
    "compTipologiaTreno": "nazionale",
    "compClassRitardoTxt": "ritardo01_txt",
    "compClassRitardoLine": "ritardo01_line",
    "compImgRitardo2": "/vt_static/img/legenda/icone_legenda/ritardo01.png",
    "compImgRitardo": "/vt_static/img/legenda/icone_legenda/ritardo01.png",
    "compRitardo": [
      "ritardo 23 min.",
      "delay 23 min.",
      "Versp&#228;tung 23 Min.",
      "retard de 23 min.",
      "retraso de 23 min.",
      "&icirc;nt&acirc;rziere 23 min.",
      "遅延 23 分",
      "误点 23分钟",
      "опоздание на 23 минут"
    ],
    "compRitardoAndamento": [
      "con un ritardo di 23 min.",
      "23 minutes late",
      "mit einer Verz&#246;gerung von 23 Min.",
      "avec un retard de 23 min.",
      "con un retraso de 23 min.",
      "cu o &icirc;nt&acirc;rziere de 23 min.",
      "23 分の遅延",
      "误点 23分钟",
      "с опозданием в 23 минут"
    ],
    "compInStazionePartenza": [
      "",
      "",
      "",
      "",
      "",
      "",
      "",
      "",
      ""
    ],
    "compInStazioneArrivo": [
      "",
      "",
      "",
      "",
      "",
      "",
      "",
      "",
      ""
    ],
    "compOrarioEffettivoArrivo": null,
    "compDurata": "",
    "compImgCambiNumerazione": "&nbsp;&nbsp;",
    "materiale_label": null,
    "dataPartenzaTreno": 1678230000000
  },
]
```

TODO documentazione.

Altri campi:
- `provvedimento`: da rilevazioni empiriche, sembra che può assumere i seguenti valori.
  - `0`: regolare;
  - `1`: treno cancellato;
  - `2`: treno parzialmente cancellato / deviato / riprogrammato;

### Esempio

> [/partenze/S01700/Wed Mar 08 2023 17:04:00 GMT+0100](http://www.viaggiatreno.it/infomobilita/resteasy/viaggiatreno/elencoStazioni/1)
> ```
> (omissis)
> ```

## `/arrivi/<IDStazione>/<orarioAttuale>`

Identico a `/partenze`.

## `/andamentoTreno/<IDStazioneOrigine>/<numeroTreno>/<orarioMezzanotte>`

### Parametri

- `IDStazioneOrigine`: ID della stazione cui il treno ha origine;
- `numeroTreno`;
- `orarioMezzanotte`: l'orario della mezzanotte del giorno in cui si fa la richiesta.

### Risposta

Nella [repo di roughconsensusandrunningcode](https://github.com/roughconsensusandrunningcode/TrainMonitor/wiki/API-del-sistema-Viaggiatreno/) sono indicate alcuni campi.

* *idOrigine* e *idDestinazione*: codici delle stazioni di partenza e destinazione
* *origine* e *destinazione*: nomi delle stazioni di partenza e destinazione
* *orarioPartenza* e *orarioArrivo*: orari programmati di partenza da *origine* e arrivo a *destinazione* in timestamp
* *compOrarioArrivo* e *compOrarioPartenza*: orari programmati di partenza da *origine* e arrivo a *destinazione* in formato HH:MM
* *compRitardo* e *compRitardoAndamento*: descrizione testuale del ritardo in varie lingue
* *oraUltimoRilevamento* e *stazioneUltimoRilevamento*: orario in timestamp e nome della stazione dell'ultimo rilevamento, valgono rispettivamente *null* e "--" se il treno non è ancora partito oppure è stato soppresso
* *origineEstera*, *destinazioneEstera*, *oraPartenzaEstera*, *oraArrivoEstera*: valorizzati solo per treni internazionali
* *tipoTreno* e *provvedimento* codificano lo stato del treno:
  * *tipoTreno* vale 'PG' e *provvedimento* vale 0: treno regolare
  * *tipoTreno* vale 'ST' e *provvedimento* vale 1: treno soppresso (in questo caso l'array *fermate* ha lunghezza 0)
  * *tipoTreno* vale 'PP' oppure 'SI' oppure 'SF' e *provvedimento* vale 0 oppure 2: treno parzialmente soppresso (in questo caso uno o più elementi dell'array *fermate* hanno il campo *actualFermataType* uguale a 3)
  * *tipoTreno* vale 'DV' e *provvedimento* vale 3: treno deviato (da approfondire)
* *subTitle* se il treno è parzialmente soppresso (*tipoTreno* in ('PP', 'SI', 'SF')) contiene una descrizione della tratta cancellata (ad esempio: *Treno cancellato da NOVI LIGURE a ALESSANDRIA. Parte da ALESSANDRIA*)
* *fermate*: array, un elemento per ogni fermata, con i seguenti campi principali:
  * *id* e *stazione*: codice e nome della stazione
  * *tipoFermata*: 'P' (stazione di origine), 'A' (stazione di destinazione), 'F' (fermata intermedia)
  * *ritardoArrivo* e *ritardoPartenza*: ritardo in minuti di arrivo e partenza alla stazione, in minuti interi
  * *ritardo*: ritardo in partenza (se *tipoFermata*=='P') e di arrivo altrimenti, in minuti interi
  * *arrivoReale* e *partenzaReale*: orari effettivi di arrivo e partenza nella stazione, in timestamp
  * *partenza_teorica* e *arrivo_teorico*: orari teorici di partenza e arrivo nella stazione, in timestamp - sono presenti dal 12 marzo 2015
  * *programmata*: orario programmato di partenza (se *tipoFermata*=='P') e di arrivo altrimenti, in timestamp
  * *programmataZero*: di solito vale *null*, è valorizzato in caso di orario riprogrammato
  * *actualFermataType*:
      * 1 fermata regolare
      * 2 fermata non prevista
      * 3 fermata soppressa (se *tipoTreno* in ('PP', 'SI', 'SF'))
      * 0 Dato non disponibile (*arrivoReale* e/o *partenzaReale* valgono *null*, può essere perché il treno è ancora in viaggio e deve ancora arrivare nella fermata oppure perché il dato non è stato rilevato)
  * *partenzaTeoricaZero* e *arrivoTeoricoZero*: da approfondire

### Caveats

- TODO: controllare comportamento parametro `orarioMezzanotte` e treni notturni.
- Alcune volte, nonostante il treno esista e sia già stato ritornato da altre chiamate API (come `partenze`), `andamentoTreno` ritorna HTTP 204.
In questo caso, i dettagli della corsa non sono semplicemente disponibili.
Spesso accade con __treni cancellati__ o __riprogrammati__.

#### Esempio di treno parzialmente cancellato

L'11 marzo 2023, il treno IC 551 è stato parzialmente cancellato:

> _**IC 551 Roma Termini (9:26) - Reggio Calabria Centrale (16:50)**: cancellato tra Salerno e Vallo della Lucania._
> _I passeggeri possono proseguire da Salerno con il treno **IC 723 Roma Termini (7:26) - Palermo Centrale (19:25)** fino a Villa San Giovanni, dove trovano ulteriore proseguimento per Reggio Calabria Centrale con i primi treni Regionali utili._
>
> __InfoMobilità dell'11 marzo 2023 ore 10:00.__

All'endpoint `/partenze` di __Napoli Centrale__ (S09218) il treno IC 551 è presente.

```json
{
  "numeroTreno": 551,
  "categoria": "IC",
  "categoriaDescrizione": "IC",
  "origine": null,
  "codOrigine": "S08409",
  "destinazione": "SALERNO",
  "codDestinazione": null,
  "origineEstera": null,
  "destinazioneEstera": null,
  "oraPartenzaEstera": null,
  "oraArrivoEstera": null,
  "tratta": 0,
  "regione": 0,
  "origineZero": null,
  "destinazioneZero": null,
  "orarioPartenzaZero": null,
  "orarioArrivoZero": null,
  "circolante": true,
  "codiceCliente": 4,
  "binarioEffettivoArrivoCodice": null,
  "binarioEffettivoArrivoDescrizione": null,
  "binarioEffettivoArrivoTipo": null,
  "binarioProgrammatoArrivoCodice": null,
  "binarioProgrammatoArrivoDescrizione": null,
  "binarioEffettivoPartenzaCodice": "507",
  "binarioEffettivoPartenzaDescrizione": "10",
  "binarioEffettivoPartenzaTipo": "0",
  "binarioProgrammatoPartenzaCodice": "0",
  "binarioProgrammatoPartenzaDescrizione": "13",
  "subTitle": null,
  "esisteCorsaZero": null,
  "orientamento": null,
  "inStazione": false,
  "haCambiNumero": false,
  "nonPartito": false,
  "provvedimento": 2,
  "riprogrammazione": "Y",
  "orarioPartenza": 1678531500000,
  "orarioArrivo": null,
  "stazionePartenza": null,
  "stazioneArrivo": null,
  "statoTreno": null,
  "corrispondenze": null,
  "servizi": null,
  "ritardo": 0,
  "tipoProdotto": "0",
  "compOrarioPartenzaZeroEffettivo": "11:45",
  "compOrarioArrivoZeroEffettivo": null,
  "compOrarioPartenzaZero": "11:45",
  "compOrarioArrivoZero": null,
  "compOrarioArrivo": null,
  "compOrarioPartenza": "11:45",
  "compNumeroTreno": "IC 551",
  "compOrientamento": [
    "--",
    "--",
    "--",
    "--",
    "--",
    "--",
    "--",
    "--",
    "--"
  ],
  "compTipologiaTreno": "nazionale",
  "compClassRitardoTxt": "",
  "compClassRitardoLine": "regolare_line",
  "compImgRitardo2": "",
  "compImgRitardo": "/vt_static/img/legenda/icone_legenda/regolare.png",
  "compRitardo": [
    "in orario",
    "on time",
    "p&#252;nktlich",
    "&agrave; l'heure",
    "en horario",
    "conform orarului",
    "定刻",
    "按时",
    "по расписанию"
  ],
  "compRitardoAndamento": [
    "in orario",
    "on time",
    "p&#252;nktlich",
    "&agrave; l'heure",
    "en horario",
    "conform orarului",
    "定刻",
    "按时",
    "по расписанию"
  ],
  "compInStazionePartenza": [
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    ""
  ],
  "compInStazioneArrivo": [
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    ""
  ],
  "compOrarioEffettivoArrivo": null,
  "compDurata": "",
  "compImgCambiNumerazione": "&nbsp;&nbsp;<img src=\"/vt_static/img/legenda/icone_legenda/riprogrammato.png\">&nbsp;<img src=\"/vt_static/img/legenda/icone_legenda/cancellazione.png\">",
  "materiale_label": null,
  "dataPartenzaTreno": 1678489200000
},
```

L'endpoint `/andamentoTreno` (con i parametri corretti) ritorna però __HTTP 204 (No Content)__.
In effetti, cercando lo stesso treno sul portale web di ViaggiaTreno la pagina fa le stesse chiamate API descritte sopra, fino ad entrare in un caricamento infinito in seguito alla ricezione di HTTP 204.

In nessun portale ufficiale e non sono reperibili le effettive informazioni del treno, escludendo presumibilmente i monitor in stazione.

Di seguito alcuni __campi notevoli__ dalla risposta di `/partenze` che possono essere utilizzati come campanelli d'allarme per rilevare questo tipo di situazioni.
- `"provvedimento": 2`, indicante _treno cancellato parzialmente_;
- `"riprogrammazione": "Y"`;
- `"compImgCambiNumerazione"` contiene dell'HTML con due immagini chiamate `riprogrammato.png` e `cancellazione.png`, che vengono effettivamente visualizzate nel portale web.
