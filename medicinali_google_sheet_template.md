# Google Sheet template: Medicinali

Questo file è un **template riusabile** per creare un Google Sheet per:
- **anagrafica farmaci** (master)
- **piano terapeutico** (orari/dosi)
- **inventario** (scorte)
- **registro** (somministrazioni reali)
- **liste** (valori per menu a tendina)

## Come usarlo (2 minuti)
1. Crea un nuovo Google Sheet.
2. Crea 5 tab con questi nomi: `FARMACI`, `POSOLOGIA`, `INVENTARIO`, `REGISTRO`, `LISTE`.
3. Per ogni tab, copia **le righe CSV** (separate da virgola) qui sotto e incollale in `A1`.
4. (Opzionale) Aggiungi **Convalida dati** usando le liste del tab `LISTE`.

> Nota: le righe sotto sono in **CSV** (colonne separate da virgola). Se Sheets non separa in colonne automaticamente: *Dati → Dividi testo in colonne* e scegli “Virgola”.

---

## Tab: `FARMACI`
**Scopo**: una riga per ogni farmaco/prodotto.

Incolla in `A1`:

```csv
farmaco_id,nome_commerciale,principio_attivo,forma,unita_dose,dose_per_unita,via,note
```

Righe create dalle 2 pagine (puoi modificarle):

```csv
F001,Eutirox,,compressa,compressa,,orale,"Appena sveglio; aspettare 30 min prima di colazione"
F002,Madopar,,compressa,compressa,,orale,
F003,Cortone acetato,,compressa,compressa,,orale,
F004,Keppra,levetiracetam,soluzione orale,ml,,orale,
F005,Lansoprazolo,,compressa,compressa,,orale,
F006,Mantadan,,compressa,compressa,,orale,
F007,Normase,lattulosio,sciroppo,ml,,orale,
F008,Redipeg,,bustina,busta,,orale,
F009,Sertralina,,compressa,compressa,,orale,
F010,Abound arancia,,bustina,busta,,orale,
F011,Tredimin,colecalciferolo,flaconcino,flaconcino,,orale,"1 flaconcino ogni mercoledì"
F012,Acido ascorbico,,fiala,fiala,,orale,
F013,Immun Age,,bustina,busta,,orale,
F014,"Amlodipina (Norvasc)",,compressa,compressa,,orale,
F015,Bisacodil,,compressa,compressa,,orale,
F016,Atorvastatina,,compressa,compressa,,orale,
F017,Enoxaparina,,siringa,siringa,,s.c.,
F018,Melatonina,,compressa,compressa,,orale,
F019,Recugel gel oculare,,gel,applicazione,,oculare,"oftalmico"
F020,VSL 3,,bustina,busta,,orale,
F021,Pineal Note,,gocce,gocce,,oculare,
F022,Hyalistil,"acido ialuronico (sale sodico)",gocce,gocce,,oculare,
F023,Tamsulosin,,compressa,compressa,,orale,
F024,Resource Instant Protein,,polvere,grammi,,orale,"ai pasti"
```

---

## Tab: `POSOLOGIA`
**Scopo**: piano terapeutico; una riga per “evento” programmato (farmaco + ora + dose + regola).

Incolla in `A1`:

```csv
posologia_id,farmaco_id,ora,dose,unita,frequenza,giorni_settimana,attivo,con_pasto,note_evento
```

Righe create dalle 2 pagine (puoi modificarle):

```csv
P001,F001,07:00,1,compressa,giornaliera,,TRUE,prima_pasto,"Appena sveglio; aspettare 30 min prima di colazione"
P002,F002,07:00,0.5,compressa,giornaliera,,TRUE,indifferente,
P003,F003,08:00,1,compressa,giornaliera,,TRUE,indifferente,
P004,F004,08:00,10,ml,giornaliera,,TRUE,indifferente,"(levetiracetam)"
P005,F005,08:00,1,compressa,giornaliera,,TRUE,indifferente,
P006,F006,08:00,1,compressa,giornaliera,,TRUE,indifferente,
P007,F007,08:00,25,ml,giornaliera,,TRUE,indifferente,"(lattulosio)"
P008,F008,08:00,1,busta,giornaliera,,TRUE,indifferente,
P009,F009,08:00,1,compressa,giornaliera,,TRUE,indifferente,
P010,F022,08:00,2,gocce,giornaliera,,TRUE,indifferente,
P011,F002,10:00,0.5,compressa,giornaliera,,TRUE,indifferente,
P012,F010,12:00,1,busta,giornaliera,,TRUE,con_pasto,
P013,F002,12:00,0.5,compressa,giornaliera,,TRUE,indifferente,
P014,F006,12:00,1,compressa,giornaliera,,TRUE,indifferente,
P015,F011,12:00,1,flaconcino,settimanale,Mer,TRUE,indifferente,"(colecalciferolo)"
P016,F012,12:00,1,fiala,giornaliera,,TRUE,indifferente,
P017,F013,12:00,1,busta,giornaliera,,TRUE,con_pasto,
P018,F002,14:00,0.5,compressa,giornaliera,,TRUE,indifferente,
P019,F014,16:00,0.5,compressa,giornaliera,,TRUE,indifferente,
P020,F003,16:00,0.5,compressa,giornaliera,,TRUE,indifferente,
P021,F022,16:00,2,gocce,giornaliera,,TRUE,indifferente,
P022,F010,18:00,1,busta,giornaliera,,TRUE,con_pasto,
P023,F015,18:00,2,compressa,giornaliera,,TRUE,indifferente,
P024,F002,18:00,0.5,compressa,giornaliera,,TRUE,indifferente,
P025,F008,18:00,1,busta,giornaliera,,TRUE,indifferente,
P026,F016,20:00,1,compressa,giornaliera,,TRUE,indifferente,
P027,F017,20:00,1,siringa,giornaliera,,TRUE,indifferente,
P028,F004,20:00,10,ml,giornaliera,,TRUE,indifferente,"(levetiracetam)"
P029,F018,20:00,1,compressa,giornaliera,,TRUE,indifferente,
P030,F007,20:00,20,ml,giornaliera,,TRUE,indifferente,"(lattulosio)"
P031,F019,20:00,1,applicazione,giornaliera,,TRUE,indifferente,"gel oculare (oftalmico)"
P032,F020,20:00,2,busta,giornaliera,,TRUE,con_pasto,
P033,F021,22:00,20,gocce,giornaliera,,TRUE,indifferente,
P034,F022,22:00,2,gocce,giornaliera,,TRUE,indifferente,
P035,F023,22:00,1,compressa,giornaliera,,TRUE,indifferente,
P036,F024,,15,grammi,giornaliera,,TRUE,con_pasto,"ai pasti"
```

> `giorni_settimana`: usa `Lun,Mar,Mer,Gio,Ven,Sab,Dom` (se vuoto = tutti i giorni).

---

## Tab: `INVENTARIO`
**Scopo**: scorte; una riga per ogni ingresso (acquisto/ricarico).

Incolla in `A1`:

```csv
mov_id,data_acquisto,data_inserimento,farmaco_id,quantita,unita_misura,pezzi_per_confezione,scadenza,lotto,posizione,note
```

Esempio (opzionale):

```csv
M001,2026-01-03,2026-01-03,F002,1,bustina,,,,"dispensa",
```

---

## Tab: `REGISTRO`
**Scopo**: log reale di somministrazioni (o dose saltata/ritardata).

Incolla in `A1`:

```csv
timestamp,farmaco_id,dose_somministrata,unita,stato,chi,posologia_id,nota
```

Esempio (opzionale):

```csv
2026-01-04 08:02,F001,10,ml,somministrato,Marco,P001,
```

---

## Tab: `LISTE`
**Scopo**: valori standard per menu a tendina (convalida dati).

Incolla in `A1`:

```csv
forme,vie,unita_dose,unita_misura_confezione,frequenze,stati,giorni_settimana,con_pasto
compressa,orale,mg,scatola,giornaliera,somministrato,Lun,prima_pasto
mezza compressa,oculare,ml,blister,settimanale,saltato,Mar,dopo_pasto
bustina,s.c.,gocce,bustina,ogni_N_giorni,ritardato,Mer,indifferente
fiala,i.m.,buste,flacone,,,,indifferente
gel,s.l.,,flaconcino,,,,
siringa,,,siringa,,,,
spray,,,,,,,
,,,,,,Sab,
,,,,,,Dom,
```

---

## Consigli rapidi (opzionali)
- **Menu a tendina**: in Sheets → *Dati → Convalida dati* → intervallo `LISTE!A2:A`, ecc.
- **Evita refusi**: usa sempre `farmaco_id` come collegamento tra tab.
- **Se vuoi “Agenda Oggi”**: crea un tab `OGGI` e usa un filtro/query su `POSOLOGIA` (attivo + giorno settimana).

