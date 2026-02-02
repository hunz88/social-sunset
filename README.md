# 🌅 Sunset Social - Marketing Strategy Monitor

Sistema automatizzato di marketing intelligence per business nel settore hospitality/food & beverage. Analizza recensioni, trend social e genera idee marketing personalizzate usando AI.

## 📋 Caratteristiche

- **🔍 Scraping Multi-Platform**: Google Maps, Instagram, TikTok, Facebook
- **🤖 AI-Powered**: Integrazione con Gemini AI per generazione idee marketing
- **📊 Dashboard Web**: Interfaccia responsive per gestire idee
- **🔐 Autenticazione**: Protezione con password
- **💾 Persistenza Dati**: Storage su file JSON con backup automatici
- **⏰ Scheduling**: Esecuzione automatica 2 volte al giorno
- **📝 Logging Strutturato**: Log dettagliati in file e console
- **🍓 Raspberry Pi Optimized**: Ottimizzato per Raspberry Pi

## 🚀 Quick Start

### Prerequisiti

- Python 3.8+
- Account Apify (per scraping)
- API Key Google Gemini (per AI)

### Installazione

1. **Clone del repository**
```bash
git clone <repo-url>
cd social-sunset
```

2. **Installa le dipendenze**
```bash
pip install -r requirements.txt
```

3. **Configura le variabili d'ambiente**
```bash
cp .env.example .env
nano .env
```

Modifica il file `.env`:
```env
# API Keys
GEMINI_API_KEY=your_gemini_api_key_here
APIFY_API_KEY=your_apify_api_key_here

# Security (IMPORTANTE: cambia in produzione!)
SECRET_KEY=your_random_secret_key_here
ADMIN_PASSWORD=your_secure_password_here

# Configuration
BUSINESS_NAME=Sunset
LOCATION=zona porto/spiaggia
COMPETITORS=Bar del Porto,Lounge Mediterraneo,Beach Club
PORT=4123
```

4. **Avvia l'applicazione**
```bash
python app.py
```

5. **Accedi alla dashboard**
Apri il browser e vai a: `http://localhost:4123`

Login con la password impostata in `ADMIN_PASSWORD`

## 📖 Configurazione Dettagliata

### Variabili d'Ambiente

| Variabile | Descrizione | Default | Obbligatorio |
|-----------|-------------|---------|--------------|
| `GEMINI_API_KEY` | API Key di Google Gemini | - | Consigliato* |
| `APIFY_API_KEY` | API Key di Apify | - | Consigliato* |
| `SECRET_KEY` | Chiave segreta Flask | Auto-generata | Sì (prod) |
| `ADMIN_PASSWORD` | Password dashboard | `sunset2024` | Sì |
| `BUSINESS_NAME` | Nome del tuo business | `Sunset` | No |
| `LOCATION` | Location geografica | `zona porto/spiaggia` | No |
| `COMPETITORS` | Competitor (CSV) | `Bar del Porto,...` | No |
| `PORT` | Porta web server | `4123` | No |

\* *Se non fornite, l'app usa dati mock per testing*

### Come Ottenere le API Keys

**Gemini API Key:**
1. Vai su [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Crea un nuovo progetto
3. Genera una API key
4. Copia la key nel `.env`

**Apify API Key:**
1. Registrati su [Apify](https://apify.com)
2. Vai su Settings > Integrations
3. Copia la tua API token
4. Incollala nel `.env`

## 🎯 Come Funziona

1. **Scraping Automatico**: Ogni giorno alle 9:00 e 14:00, il sistema:
   - Scrapa recensioni da Google Maps (tue e competitor)
   - Analizza trend visivi su Instagram/TikTok
   - Monitora eventi locali su Facebook

2. **Generazione Idee AI**: Gemini analizza i dati e genera:
   - 3 idee marketing personalizzate
   - Testi post pronti all'uso
   - Suggerimenti media (foto, video, reel)
   - Piattaforma consigliata

3. **Review & Approvazione**: Tramite dashboard:
   - Visualizzi le idee pending
   - Approvi quelle che ti piacciono
   - Scarti quelle non rilevanti

4. **Export**: Le idee approvate vengono salvate in:
   - `~/SunsetSocial/post_pronti/` come file JSON
   - Pronti per essere implementati

## 📁 Struttura Directory

```
social-sunset/
├── app.py                 # Applicazione principale
├── auth.py               # Sistema autenticazione
├── storage.py            # Persistenza dati
├── requirements.txt      # Dipendenze Python
├── .env                  # Configurazione (non in git)
├── .env.example          # Template configurazione
├── templates/
│   └── dashboard.html    # Dashboard web
└── scrapers/
    ├── base.py           # Classe base scrapers
    ├── google_maps.py    # Scraper Google Maps
    ├── instagram.py      # Scraper Instagram
    ├── tiktok.py         # Scraper TikTok
    └── facebook.py       # Scraper Facebook

Runtime directories (auto-create):
~/SunsetSocial/
├── data/
│   ├── logs/             # Log files
│   ├── pending_ideas.json
│   ├── approved_ideas.json
│   ├── backups/          # Backup automatici
│   └── scraped_*.json    # Dati scraped
└── post_pronti/          # Idee approvate (export)
```

## 🔧 Deployment su Raspberry Pi

### Setup Raspberry Pi

1. **Update sistema**
```bash
sudo apt update && sudo apt upgrade -y
```

2. **Installa Python 3**
```bash
sudo apt install python3 python3-pip -y
```

3. **Clone e setup**
```bash
cd ~
git clone <repo-url> social-sunset
cd social-sunset
pip3 install -r requirements.txt
```

4. **Configura .env**
```bash
cp .env.example .env
nano .env
# Imposta le API keys e password
```

5. **Test run**
```bash
python3 app.py
```

### Autostart con systemd

Crea un service file:
```bash
sudo nano /etc/systemd/system/sunset-social.service
```

Contenuto:
```ini
[Unit]
Description=Sunset Social Monitor
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/social-sunset
Environment="PATH=/usr/bin"
ExecStart=/usr/bin/python3 /home/pi/social-sunset/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Abilita e avvia:
```bash
sudo systemctl daemon-reload
sudo systemctl enable sunset-social
sudo systemctl start sunset-social
sudo systemctl status sunset-social
```

Visualizza log:
```bash
sudo journalctl -u sunset-social -f
```

### Accesso da Rete Locale

1. Trova IP del Raspberry Pi:
```bash
hostname -I
```

2. Accedi da altro device:
```
http://192.168.1.XXX:4123
```

## 🛡️ Sicurezza

### Raccomandazioni Produzione

1. **Cambia le password default**
   - Imposta `ADMIN_PASSWORD` forte
   - Genera `SECRET_KEY` casuale (32+ caratteri)

2. **Limita accesso rete**
   - Usa firewall per limitare accesso a IP fidati
   - Considera reverse proxy (nginx) con HTTPS

3. **Backup regolari**
   - I backup vengono creati automaticamente in `~/SunsetSocial/data/backups/`
   - Considera backup esterni periodici

4. **Aggiorna regolarmente**
```bash
cd social-sunset
git pull
pip install -r requirements.txt --upgrade
sudo systemctl restart sunset-social
```

## 📊 Monitoraggio

### Log Files

I log sono salvati in: `~/SunsetSocial/data/logs/sunset_social_YYYYMMDD.log`

Visualizza log real-time:
```bash
tail -f ~/SunsetSocial/data/logs/sunset_social_$(date +%Y%m%d).log
```

### Endpoints API

| Endpoint | Metodo | Descrizione |
|----------|--------|-------------|
| `/` | GET | Dashboard principale |
| `/login` | GET/POST | Login page |
| `/logout` | GET | Logout |
| `/api/approve/<id>` | POST | Approva idea |
| `/api/reject/<id>` | POST | Rifiuta idea |
| `/api/run-now` | POST | Esegui scrapers manualmente |
| `/api/stats` | GET | Statistiche JSON |

## 🐛 Troubleshooting

### App non si avvia

```bash
# Verifica dipendenze
pip install -r requirements.txt

# Verifica .env
cat .env

# Verifica log
python3 app.py
```

### Scrapers non funzionano

- Verifica che le API keys siano corrette
- Controlla i log per errori specifici
- Gli scrapers falliscono? L'app usa dati mock automaticamente

### Password dimenticata

Modifica `ADMIN_PASSWORD` nel file `.env` e riavvia:
```bash
nano .env
# Cambia ADMIN_PASSWORD
sudo systemctl restart sunset-social  # Se usi systemd
# oppure
pkill python3 && python3 app.py  # Manuale
```

### Porta già in uso

Cambia porta nel `.env`:
```bash
PORT=8080
```

## 🤝 Contributing

Contributi benvenuti! Per bug report o feature request, apri una issue.

## 📝 License

Progetto privato - Tutti i diritti riservati.

## 📞 Support

Per supporto o domande, contatta il maintainer.

---

**Made with ❤️ for Sunset Social Marketing**
