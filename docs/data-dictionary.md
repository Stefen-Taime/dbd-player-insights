# Data Dictionary

## Event Types

| Event | Table RAW | Description | Volume estime |
|---|---|---|---|
| match_completed | RAW_MATCH_COMPLETED | Fin de match avec stats killer/survivors | ~100k/jour |
| session_event | RAW_SESSION_EVENT | Login, logout, queue, match start/end, store visit | ~500k/jour |
| store_transaction | RAW_STORE_TRANSACTION | Achats en magasin (cosmetics, DLC, rift pass) | ~10k/jour |
| mmr_update | RAW_MMR_UPDATE | Mise a jour MMR apres chaque match | ~200k/jour |
| player_registration | RAW_PLAYER_REGISTRATION | Inscription d'un nouveau joueur | ~5k/jour |
| progression_event | RAW_PROGRESSION_EVENT | Bloodpoints, prestige, perk unlocks | ~300k/jour |

## Champs cles

### match_completed
- `event_id` (VARCHAR) : identifiant unique de l'evenement
- `match_id` (VARCHAR) : identifiant du match
- `timestamp` (TIMESTAMP_NTZ) : horodatage
- `duration_seconds` (INT) : duree du match
- `map_id` (VARCHAR) : identifiant de la map
- `game_mode` (VARCHAR) : public, custom, ranked
- `killer` (OBJECT) : player_id, character_id, perks[], kills, hooks, score
- `survivors` (ARRAY) : [{player_id, character_id, perks[], escaped, generators_completed, score}]

### session_event
- `player_id` (VARCHAR) : identifiant du joueur
- `session_id` (VARCHAR) : identifiant de la session
- `action` (VARCHAR) : login, logout, queue_join, match_start, match_end, store_visit
- `platform` (VARCHAR) : steam, ps5, xbox, switch, epic
- `region` (VARCHAR) : us-east-1, eu-west-1, ap-northeast-1

### store_transaction
- `transaction_id` (VARCHAR) : identifiant unique de la transaction
- `item_id` (VARCHAR) : identifiant de l'item achete
- `item_type` (VARCHAR) : cosmetic, dlc, rift_pass, auric_cells
- `currency` (VARCHAR) : auric_cells, iridescent_shards, usd
- `amount_usd` (NUMBER) : montant en USD
