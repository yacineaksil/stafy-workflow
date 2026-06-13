# stafy-workflow

Détecteur de **value bets** pour le football, le baseball (MLB) et le basket (NBA),
à partir des données réelles d'[API-Sports](https://api-sports.io) et des cotes
**1xBet**.

## La stratégie en une phrase

On ne parie **pas** sur l'issue la plus probable, mais sur celle dont la
probabilité estimée par notre modèle dépasse la probabilité implicite des cotes.
C'est la seule approche rentable à long terme, car le bookmaker intègre une
marge (`overround`) dans chaque cote.

```
value = proba_modèle × cote − 1     →  on parie si value > seuil (défaut 5%)
mise  = Kelly fractionné (¼ Kelly)  →  gère la bankroll sans tout risquer
```

## Comment ça marche

```
match (id) ──> API-Sports (fixtures + stats + cotes)
            ──> modèle de proba propre au sport
            ──> comparaison aux cotes 1xBet (marge retirée)
            ──> value bets triés, avec mise Kelly recommandée
```

Un modèle par sport, car chacun a sa physique statistique :

| Sport     | Modèle                                   | Source de données        | Limite assumée                          |
|-----------|------------------------------------------|--------------------------|-----------------------------------------|
| Football  | Poisson bivarié + correction Dixon-Coles | Stats de buts par lieu   | Pas de normalisation de ligue           |
| Baseball  | log5 sur win % + avantage terrain        | Classements (standings)  | **Sans lanceur partant** (très impactant)|
| Basket    | Pythagore sur points + log5              | Classements (standings)  | Sans ajustement de pace / repos         |

## Installation

```bash
python3 -m pip install -r requirements.txt
cp .env.example .env        # puis renseigne ta clé API-Sports dans .env
```

Le fichier `.env` est **ignoré par git** : ta clé n'est jamais committée.

## Utilisation

```bash
# un match
python cli.py football 1035000

# plusieurs matchs, plusieurs sports, avec bankroll pour chiffrer les mises
python cli.py football 1035000 baseball 7890 basketball 12345 --bankroll 200
```

Les `match_id` se récupèrent via les endpoints `fixtures` (foot) / `games`
(baseball, basket) d'API-Sports.

## ⚠️ Réseau (Claude Code web)

Depuis le sandbox Claude Code sur le web, les hôtes `*.api-sports.io` sont
**bloqués** par la politique d'egress. Pour récupérer les vraies données :

- lance l'outil **sur ta machine**, ou
- ajoute les hôtes à l'allowlist d'egress de l'environnement
  ([doc](https://code.claude.com/docs/en/claude-code-on-the-web)) :
  `v3.football.api-sports.io`, `v1.baseball.api-sports.io`,
  `v1.basketball.api-sports.io`.

## ⚠️ Honnêteté sur les attentes

- **Aucun outil ne garantit de gagner.** Les marchés majeurs sont quasi
  efficients ; l'edge réel est mince et se trouve surtout sur les ligues/marchés
  secondaires.
- 1xBet **limite ou ferme** les comptes gagnants.
- La qualité vient des **données et de la calibration**, pas de la complexité.
  Prochaine étape la plus rentable : ajouter le **lanceur partant** (MLB) et le
  **pace** (NBA), puis **backtester** sur l'historique avant de miser réellement.
- À jouer uniquement si le pari sportif est légal chez toi, avec de l'argent que
  tu peux perdre.

## Tests

```bash
python -m pytest -q
```

## Structure

```
stafy/
├── config.py       # config via .env
├── api_client.py   # client API-Sports (3 sports)
├── odds.py         # extraction des cotes 1xBet
├── value.py        # proba implicite, marge, value, Kelly
├── models/         # football.py · baseball.py · basketball.py
└── pipeline.py     # orchestration match -> recommandations
cli.py              # point d'entrée
tests/              # logique pure testée hors-ligne
```
