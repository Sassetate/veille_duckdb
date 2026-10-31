# veille_duckdb

Workflow Mistral (managed deployment) : envoi chaque lundi à 8h00 (Europe/Paris) d un récapitulatif des nouveautés DuckDB par email à johanguely@live.fr, uniquement s il y a des nouveautés.

## Fonctionnement
- fetch_duckdb_news : releases GitHub duckdb/duckdb + blog duckdb.org (7 derniers jours)
- summarize_news : résumé en français via l API Mistral
- send_email : envoi via Microsoft Graph (GRAPH_ACCESS_TOKEN, destinataire MAIL_RECIPIENT)

## Déploiement
1. Pousser ce projet sur la branche main du dépôt.
2. Installer la Mistral GitHub App (github.com/apps/mistralai) sur le dépôt.
3. Créer le managed deployment dans Mistral Studio depuis ce dépôt.
4. Planifier : cron "0 8 * * 1", fuseau Europe/Paris.
