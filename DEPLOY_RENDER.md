# Guida al Deploy su Render.com

## Istruzioni per il Deploy del Sito con AdSense

Dopo aver aggiunto il codice di verifica AdSense, segui questi passaggi per fare il deploy su Render.

### Opzione 1: Deploy Automatico (Consigliato)

Se hai già configurato il deploy automatico da GitHub/GitLab:

1. **Commit delle modifiche**
   ```bash
   git add frontend/app/layout.tsx ADSENSE_SETUP.md DEPLOY_RENDER.md
   git commit -m "Aggiunto codice verifica AdSense"
   git push origin main
   ```

2. **Render farà automaticamente il deploy**
   - Vai su [Render Dashboard](https://dashboard.render.com/)
   - Controlla lo stato del deploy nella sezione "Events"
   - Attendi il completamento (di solito 2-5 minuti)

### Opzione 2: Deploy Manuale

Se preferisci fare il deploy manualmente:

1. **Accedi a Render Dashboard**
   - Vai su https://dashboard.render.com/
   - Seleziona il tuo servizio web

2. **Trigger Manual Deploy**
   - Clicca su "Manual Deploy"
   - Seleziona "Deploy latest commit"
   - Oppure seleziona "Clear build cache & deploy" se hai problemi

3. **Monitora il Deploy**
   - Controlla i log in tempo reale
   - Verifica che il build completi con successo

### Configurazione Render per Next.js

Assicurati che il tuo servizio Render abbia queste impostazioni:

```yaml
# render.yaml (se usi Infrastructure as Code)
services:
  - type: web
    name: music-text-generator
    env: node
    region: frankfurt  # o la tua regione preferita
    buildCommand: cd frontend && npm install && npm run build
    startCommand: cd frontend && npm start
    envVars:
      - key: NODE_VERSION
        value: 18.17.0
```

Oppure nelle impostazioni del dashboard:

- **Build Command**: `cd frontend && npm install && npm run build`
- **Start Command**: `cd frontend && npm start`
- **Environment**: Node
- **Node Version**: 18.17.0 o superiore

### Verifica Post-Deploy

1. **Controlla il sito live**
   - Apri l'URL del tuo sito su Render (es: `https://tuo-sito.onrender.com`)
   - Verifica che il sito si carichi correttamente

2. **Ispeziona il codice HTML**
   - Premi F12 per aprire gli Strumenti per Sviluppatori
   - Vai alla tab "Elements"
   - Cerca nel `<head>` lo script AdSense:
   ```html
   <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-2145959534306055" crossorigin="anonymous"></script>
   ```

3. **Verifica su Google AdSense**
   - Vai su https://www.google.com/adsense/
   - Sezione "Siti" → "Verifica proprietà"
   - Clicca su "Verifica"
   - Attendi la conferma (può richiedere alcuni minuti)

### Comandi Git Utili

```bash
# Verifica lo stato dei file modificati
git status

# Aggiungi tutti i file modificati
git add .

# Commit con messaggio descrittivo
git commit -m "Aggiunto codice verifica AdSense per monetizzazione"

# Push al repository remoto
git push origin main

# Verifica l'ultimo commit
git log -1

# Verifica il branch corrente
git branch
```

### Troubleshooting

#### Il deploy fallisce
- Controlla i log su Render Dashboard
- Verifica che `package.json` sia corretto
- Assicurati che tutte le dipendenze siano installate
- Prova "Clear build cache & deploy"

#### Lo script AdSense non appare
- Svuota la cache del browser (Ctrl+Shift+Delete)
- Verifica che il deploy sia completato con successo
- Controlla che non ci siano errori nella console del browser
- Attendi qualche minuto per la propagazione CDN

#### Errori di verifica AdSense
- Attendi 24-48 ore dopo il primo deploy
- Verifica che il sito sia pubblicamente accessibile
- Controlla che l'URL su AdSense corrisponda a quello su Render
- Assicurati che non ci siano redirect che rimuovono lo script

### Monitoraggio Deploy

Render fornisce:
- **Logs in tempo reale**: Visualizza l'output del build e del server
- **Metrics**: CPU, memoria, richieste HTTP
- **Events**: Storico dei deploy e degli eventi

### Best Practices

1. **Usa variabili d'ambiente** per configurazioni sensibili
2. **Abilita auto-deploy** per deploy automatici ad ogni push
3. **Configura health checks** per monitorare la disponibilità
4. **Usa un dominio personalizzato** per un aspetto più professionale
5. **Abilita HTTPS** (Render lo fa automaticamente)

### Prossimi Passi dopo la Verifica

Una volta verificato il sito su AdSense:

1. **Configura le unità pubblicitarie**
   - Auto ads (consigliato per iniziare)
   - Display ads
   - In-feed ads
   - In-article ads

2. **Ottimizza il posizionamento**
   - Testa diverse posizioni
   - Monitora le performance
   - Rispetta le policy di AdSense

3. **Monitora le metriche**
   - Impressioni
   - Click-through rate (CTR)
   - Guadagni stimati
   - RPM (Revenue per Mille)

## Link Utili

- [Render Dashboard](https://dashboard.render.com/)
- [Render Docs - Next.js](https://render.com/docs/deploy-nextjs-app)
- [Google AdSense](https://www.google.com/adsense/)
- [AdSense Help Center](https://support.google.com/adsense/)

---

**Nota**: Render offre un piano gratuito con alcune limitazioni. Per siti con traffico elevato, considera l'upgrade a un piano a pagamento.