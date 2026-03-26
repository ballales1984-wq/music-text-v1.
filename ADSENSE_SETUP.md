# Configurazione AdSense - Verifica Proprietà Sito

## Modifiche Effettuate

### File Modificato: `frontend/app/layout.tsx`

È stato aggiunto il codice di verifica AdSense al layout principale dell'applicazione Next.js.

#### Modifiche Implementate:

1. **Import del componente Script di Next.js**
   ```typescript
   import Script from 'next/script'
   ```

2. **Aggiunta dello script AdSense nel `<head>`**
   ```tsx
   <head>
     <Script
       async
       src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-2145959534306055"
       crossOrigin="anonymous"
       strategy="afterInteractive"
     />
   </head>
   ```

### Dettagli Tecnici

- **Publisher ID**: `ca-pub-2145959534306055`
- **Metodo di verifica**: Snippet di codice AdSense (Meta tag)
- **Posizionamento**: Layout root (`frontend/app/layout.tsx`)
- **Copertura**: Tutte le pagine del sito

### Vantaggi dell'Implementazione

1. **Componente Script di Next.js**: Utilizza il componente ottimizzato di Next.js per il caricamento degli script
2. **Strategy "afterInteractive"**: Lo script viene caricato dopo che la pagina diventa interattiva, migliorando le performance
3. **Caricamento Asincrono**: L'attributo `async` garantisce che lo script non blocchi il rendering della pagina
4. **Cross-Origin**: L'attributo `crossOrigin="anonymous"` gestisce correttamente le richieste cross-origin

## Prossimi Passi per la Verifica

### 1. Build e Deploy

```bash
# Nella directory frontend
cd frontend
npm run build
npm start
```

Oppure, se usi un servizio di hosting (Vercel, Netlify, ecc.):
- Fai il commit delle modifiche
- Pusha su GitHub/GitLab
- Il deploy automatico si attiverà

### 2. Verifica su Google AdSense

1. Accedi alla [Console AdSense](https://www.google.com/adsense/)
2. Vai alla sezione "Siti"
3. Clicca su "Verifica proprietà del sito"
4. Seleziona il metodo "Snippet di codice AdSense"
5. Clicca su "Verifica"

**Nota**: La verifica può richiedere alcuni minuti dopo il deploy del sito.

### 3. Controllo Manuale

Dopo il deploy, puoi verificare che lo script sia presente:

1. Apri il tuo sito in un browser
2. Apri gli Strumenti per Sviluppatori (F12)
3. Vai alla tab "Elements" o "Ispeziona"
4. Cerca nel `<head>` lo script:
   ```html
   <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-2145959534306055" crossorigin="anonymous"></script>
   ```

## Risoluzione Problemi

### Lo script non appare nel sito
- Verifica che il build sia stato completato con successo
- Assicurati di aver fatto il deploy della versione aggiornata
- Svuota la cache del browser (Ctrl+F5)

### Errore di verifica su AdSense
- Attendi 24-48 ore dopo il deploy
- Verifica che il sito sia pubblicamente accessibile
- Controlla che non ci siano errori nella console del browser

### Errori di Build
Se il build fallisce, verifica:
- La sintassi del codice TypeScript
- Le dipendenze di Next.js siano installate correttamente
- La versione di Node.js sia compatibile (>= 18.17.0)

## Comandi Utili

```bash
# Build di produzione
cd frontend
npm run build

# Avvio server di produzione locale
npm start

# Sviluppo locale
npm run dev

# Verifica errori di linting
npm run lint
```

## Note Importanti

- Lo script AdSense è ora presente su **tutte le pagine** del sito
- Il codice è ottimizzato per le performance grazie al componente Script di Next.js
- La verifica della proprietà è necessaria solo una volta
- Dopo la verifica, potrai iniziare a configurare gli annunci pubblicitari

## Data Implementazione

**Data**: 26 Marzo 2026  
**Versione Next.js**: 14.2.3  
**File Modificati**: 1 (frontend/app/layout.tsx)

---

Per qualsiasi problema o domanda, consulta la [documentazione ufficiale di Google AdSense](https://support.google.com/adsense/).