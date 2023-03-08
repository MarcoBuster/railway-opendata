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
- `numeroTreno`: il numero di treno richiesto;

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
