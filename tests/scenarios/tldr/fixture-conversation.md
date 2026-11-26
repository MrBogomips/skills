# Conversation so far (you are the assistant)

**User:** Abbiamo migrato la tabella `users` a `users_v2` ieri sera. Puoi verificare com'è andata e dirmi cosa resta da fare?

**Assistant:** Ho controllato lo stato della migrazione su staging e produzione. Ecco cosa ho trovato.

Su staging la migrazione è completa: lo script `migrate_users.py` ha copiato 1.248.331 righe, il conteggio coincide con la tabella sorgente e i 412 test di integrazione passano. Ho confrontato a campione 5.000 righe campo per campo: nessuna differenza, a parte il campo `last_login`, che in `users_v2` è in UTC mentre prima era in ora locale. È voluto, ma il frontend lo mostra ancora come ora locale, quindi gli utenti vedranno un orario sbagliato di una o due ore. Ho aperto la issue #881 e preparato una patch nel branch `fix/last-login-tz`, non ancora revisionata.

In produzione la copia si è fermata al 93%: il job è stato interrotto alle 02:14 dal timeout di 4 ore del cron. Le righe copiate sono 1.161.000 circa su 1.248.000. Lo script è idempotente, quindi si può rilanciare con `--resume`, ma va deciso se farlo stanotte o subito: durante la copia le scritture su `users` sono rallentate del 30% circa per via dei trigger di doppia scrittura.

Il flag `USE_USERS_V2` è ancora spento in produzione, quindi nessun utente legge dalla nuova tabella. Il rollback, se servisse, consiste solo nel lasciare spento il flag e rimuovere i trigger; non ho ancora verificato che lo script di rimozione dei trigger funzioni in produzione, l'ho provato solo su staging.

Restano da decidere due cose: quando rilanciare la copia in produzione, e se attivare il flag su staging per un test con utenti interni prima di produzione. Io consiglierei di rilanciare stanotte alle 23 con timeout a 6 ore e di attivare il flag su staging domani. Infine c'è il tema del backup: l'ultimo snapshot di `users` è di tre giorni fa; prima di attivare il flag in produzione andrebbe fatto uno snapshot fresco.
