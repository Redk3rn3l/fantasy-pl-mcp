# Fantasy Premier League API Documentation

Complete HTTP API for all Fantasy Premier League data and tools - perfect for n8n integration.

## Base URL
```
http://172.105.168.35:8080
```

## 📊 Resources (GET Endpoints)

### Players
| Endpoint | Description | Parameters | Example |
|----------|-------------|------------|---------|
| `GET /players` | Get all players with filtering | `position`, `team`, `min_price`, `max_price`, `limit` | `/players?position=midfielder&min_price=5&limit=10` |
| `GET /player/{name}` | Find player by name | - | `/player/Salah` |
| `GET /player/{name}/fixtures` | Player's upcoming fixtures | `num_fixtures` | `/player/Salah/fixtures?num_fixtures=5` |

### Teams
| Endpoint | Description | Parameters | Example |
|----------|-------------|------------|---------|
| `GET /teams` | Get all Premier League teams | - | `/teams` |
| `GET /team/{name}` | Find team by name | - | `/team/Arsenal` |

### Gameweeks
| Endpoint | Description | Parameters | Example |
|----------|-------------|------------|---------|
| `GET /gameweek` | Current gameweek info | - | `/gameweek` |
| `GET /gameweeks` | All gameweeks data | - | `/gameweeks` |
| `GET /gameweek-status` | Detailed gameweek status | - | `/gameweek-status` |

### Fixtures
| Endpoint | Description | Parameters | Example |
|----------|-------------|------------|---------|
| `GET /fixtures` | All fixtures | `gameweek`, `team_name` | `/fixtures?gameweek=2` |
| `GET /fixtures/gameweek/{id}` | Fixtures for specific gameweek | - | `/fixtures/gameweek/2` |
| `GET /fixtures/team/{name}` | Fixtures for specific team | - | `/fixtures/team/Arsenal` |

### Special Gameweeks
| Endpoint | Description | Parameters | Example |
|----------|-------------|------------|---------|
| `GET /blank-gameweeks` | Blank gameweeks info | `num_gameweeks` | `/blank-gameweeks?num_gameweeks=10` |
| `GET /double-gameweeks` | Double gameweeks info | `num_gameweeks` | `/double-gameweeks?num_gameweeks=10` |

## 🛠️ Analysis Tools (POST Endpoints)

### Player Analysis
```http
POST /analyze/player-fixtures
Content-Type: application/json

{
  "player_name": "Salah",
  "num_fixtures": 5
}
```

### Advanced Player Analysis
```http
POST /analyze/players
Content-Type: application/json

{
  "position": "midfielder",
  "team": "Liverpool", 
  "min_price": 5.0,
  "max_price": 15.0,
  "min_points": 20,
  "min_ownership": 5,
  "max_ownership": 50,
  "form_threshold": 3.0,
  "sort_by": "points",
  "sort_order": "desc",
  "limit": 10
}
```

### Player Comparison
```http
POST /compare-players
Content-Type: application/json

{
  "player_names": ["Salah", "Haaland", "Son"],
  "metrics": ["points", "form", "goals", "assists", "bonus"]
}
```

### Fixture Analysis
```http
POST /analyze/fixtures
Content-Type: application/json

{
  "entity_type": "player",
  "entity_name": "Salah",
  "num_gameweeks": 5
}
```

## 🔐 Authentication Endpoints (GET)

**Note**: These require FPL credentials to be configured

| Endpoint | Description | Example |
|----------|-------------|---------|
| `GET /auth/check` | Check authentication status | `/auth/check` |
| `GET /auth/my-team` | Get your FPL team | `/auth/my-team` |
| `GET /auth/team/{id}` | Get any team by ID | `/auth/team/123456` |
| `GET /auth/manager` | Get manager details | `/auth/manager` |

## 📝 Prompt Templates (GET)

### Transfer Advice
```
GET /prompts/transfer_advice?budget=8.5&position=midfielder
```

### Player Analysis
```
GET /prompts/player_analysis?player_name=Salah
```

### Team Rating
```
GET /prompts/team_rating?player_list=Salah,Haaland,Son&budget=2.5
```

### Differential Players
```
GET /prompts/differential_players?max_ownership=5&budget=6
```

### Chip Strategy
```
GET /prompts/chip_strategy?available_chips=Wildcard,Bench Boost
```

## 🎯 n8n Integration Examples

### Simple HTTP Request (GET)
```javascript
// Node: HTTP Request
{
  "method": "GET",
  "url": "http://172.105.168.35:8080/players",
  "options": {
    "qs": {
      "position": "midfielder",
      "limit": 10
    }
  }
}
```

### HTTP Request with JSON Body (POST)
```javascript
// Node: HTTP Request
{
  "method": "POST",
  "url": "http://172.105.168.35:8080/compare-players",
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {
    "player_names": ["Salah", "Haaland"],
    "metrics": ["points", "goals", "assists"]
  }
}
```

### Process Response Data
```javascript
// Node: Code
const players = $json.players;
const topPlayers = players
  .filter(p => p.points > 20)
  .slice(0, 5)
  .map(p => ({
    name: p.name,
    team: p.team,
    points: p.points,
    price: p.price,
    form: p.form
  }));

return topPlayers;
```

## 🔧 Common Workflows

### 1. Find Best Value Players
```
GET /players?min_price=4&max_price=7&limit=20
→ Filter by points > 15
→ Sort by value (points/price)
```

### 2. Compare Strikers
```
POST /compare-players
{
  "player_names": ["Haaland", "Kane", "Wilson"],
  "metrics": ["points", "goals", "expected_goals", "price"]
}
```

### 3. Check Upcoming Fixtures
```
GET /player/Salah/fixtures
→ Check difficulty ratings
→ Count home vs away games
```

### 4. Find Differentials
```
GET /players?max_ownership=5&min_points=10&limit=15
→ Filter by position
→ Check upcoming fixtures
```

## 📋 Response Format

All endpoints return JSON with consistent structure:

```json
{
  "players": [...],
  "total_found": 150,
  "filters_applied": {...}
}
```

Error responses:
```json
{
  "detail": "Error message"
}
```

## 🚀 Getting Started

1. **Health Check**: `GET /health`
2. **List Players**: `GET /players?limit=5`
3. **Find Player**: `GET /player/Salah`
4. **Check Gameweek**: `GET /gameweek`
5. **Compare Players**: `POST /compare-players`

## 📊 Data Fields

### Player Object
```json
{
  "id": 531,
  "name": "Mohamed Salah",
  "web_name": "Salah",
  "team": "Liverpool",
  "team_short": "LIV", 
  "position": "MID",
  "price": 12.8,
  "form": "6.0",
  "points": 45,
  "goals": 8,
  "assists": 5,
  "bonus": 12,
  "selected_by_percent": "35.2",
  "expected_goals": "0.91",
  "expected_assists": "0.15",
  "status": "a"
}
```

### Fixture Object
```json
{
  "gameweek": 2,
  "opponent": "Arsenal", 
  "location": "home",
  "difficulty": 4,
  "kickoff_time": "2024-08-24T14:00:00Z"
}
```

---

**All MCP resources, tools, and prompts are now available as simple HTTP endpoints for easy n8n integration!** 🎯