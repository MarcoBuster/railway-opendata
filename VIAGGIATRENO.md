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
- `IDStazione`: l'ID in formato inalterato.

### Risposta
Codice della regione di appartenenza della stazione.

Una lista esaustiva dei codici è reperibile nella [repo di Razorphyn](https://github.com/Razorphyn/Informazioni-Treni-Italiani/blob/master/ID_REGIONI.csv).

### Caveats
- Il server imposta l'header `Content-Type` a `application/json`, ma il risultato non è JSON;
- I codici 21 e 22 fanno entrambi riferimento al Trentino-Alto Adige.

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
    - `1`: con alta velocità;
    - `4`: placeholder, da ignorare.
- `localita` contiene le stesse info del JSON restituito da `cercaStazione`;
- l'intuito porta a pensare che `codiceStazione`, `codStazione` e `localita.id` siano sempre uguali: non sono stati ancora trovati controesempi.

### Caveats

- `nomeCitta` può essere nullo o `"A"` (stesso significato);
- a differenza del metodo `cercaStazione`, tutte le stazioni sembrano essere presenti.

### Esempio

> [elencoStazioni/1](http://www.viaggiatreno.it/infomobilita/resteasy/viaggiatreno/elencoStazioni/1) (Lombardia)
> ```
> (omissis)
> ```

