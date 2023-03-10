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

### Esempio

> [/partenze/S01700/Wed Mar 08 2023 17:04:00 GMT+0100](http://www.viaggiatreno.it/infomobilita/resteasy/viaggiatreno/elencoStazioni/1)
> ```
> (omissis)
> ```

## `/arrivi/<IDStazione>/<orarioAttuale>`

Identico a `/partenze`.
