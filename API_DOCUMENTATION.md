# API Documentation - Project Chimera

**Version:** 1.0  
**Base URL:** `http://localhost:8000`

## Table of Contents
- [Authentication](#authentication)
- [Guardian Endpoints](#guardian-endpoints)
- [Admin Endpoints](#admin-endpoints)
- [Query Endpoints](#query-endpoints)
- [Error Codes](#error-codes)

---

## Authentication

Currently, the API does not require authentication. For production deployment, implement API keys or OAuth2.

---

## Guardian Endpoints

### POST /api/recommend

Generate team recommendations based on requirements.

**Request Body:**
```json
{
  "requisitos_hard": {
    "skills": ["Python", "Docker", "Kubernetes"]
  },
  "k": 5,
  "mission_profile": "entrega_rapida",
  "week": "2025-W01",
  "min_hours": 25,
  "force_include": ["emp_abc123"],
  "force_exclude": ["emp_xyz789"]
}
```

**Parameters:**
- `requisitos_hard.skills` (array, required): List of required skills
- `k` (integer, required): Team size
- `mission_profile` (string, optional): Mission context (`mantenimiento`, `innovacion`, `entrega_rapida`). Default: `mantenimiento`
- `week` (string, optional): ISO week for availability filter (e.g., `2025-W01`)
- `min_hours` (integer, optional): Minimum hours required per week. Default: 20
- `force_include` (array, optional): Employee IDs to force-include
- `force_exclude` (array, optional): Employee IDs to force-exclude

**Response:**
```json
{
  "request_id": "abc-123-def-456",
  "dossiers": [
    {
      "title": "The Safe Bet",
      "description": "High-skill, high-availability team optimized for reliable delivery.",
      "executive_summary": {
        "pros": [
          "✅ High average skill level (4.3/5.0)",
          "✅ All members have good availability (30+ hrs/week)",
          "✅ No critical dependencies (low Bus Factor risk)"
        ],
        "cons": [],
        "recommendation": "APPROVE"
      },
      "team": [
        {
          "id": "emp_a1b2c3d4e5f6g7h8",
          "skills_matched": ["Python", "Docker", "Kubernetes"],
          "score": 4.5,
          "availability_hours": 35,
          "conflict_risk": false,
          "linchpin_risk": "LOW"
        }
      ],
      "total_score": 21.5,
      "risk_analysis": [
        "✅ All members have strong skill levels",
        "✅ High availability ensures focus",
        "⚠️ May lack diversity in experience levels"
      ],
      "rationale": "This team prioritizes proven expertise and time commitment."
    }
  ]
}
```

**Status Codes:**
- `200 OK`: Success
- `400 Bad Request`: Invalid parameters
- `500 Internal Server Error`: Server error

---

### GET /api/linchpins

Get list of critical employees (linchpins) with Bus Factor risk.

**Response:**
```json
{
  "linchpins": [
    {
      "id": "emp_a1b2c3d4e5f6g7h8",
      "centrality_score": 0.85,
      "unique_skills": ["Terraform", "AWS Lambda"],
      "risk_level": "CRITICAL",
      "recommendation": "🚨 URGENT: Cross-train others on Terraform, AWS Lambda. High Bus Factor risk."
    },
    {
      "id": "emp_x9y8z7w6v5u4t3s2",
      "centrality_score": 0.62,
      "unique_skills": ["GraphQL"],
      "risk_level": "HIGH",
      "recommendation": "⚠️ Consider knowledge transfer sessions or pair programming."
    }
  ],
  "count": 2
}
```

**Risk Levels:**
- `CRITICAL`: High centrality (>0.7) + unique skills
- `HIGH`: High centrality (>0.5) OR multiple unique skills
- `MEDIUM`: Medium centrality (>0.3) OR has unique skills
- `LOW`: No significant risk

**Status Codes:**
- `200 OK`: Success
- `500 Internal Server Error`: Server error

---

### GET /api/mission-profiles

Get available mission profiles.

**Response:**
```json
{
  "profiles": [
    {
      "id": "mantenimiento",
      "name": "Maintenance",
      "description": "Stability and reliability over speed. Prioritizes experienced team members.",
      "strategy_preference": "safe_bet",
      "color": "#4CAF50"
    },
    {
      "id": "innovacion",
      "name": "Innovation",
      "description": "Experimentation and learning. Encourages knowledge sharing and growth.",
      "strategy_preference": "growth",
      "color": "#2196F3"
    },
    {
      "id": "entrega_rapida",
      "name": "Fast Delivery",
      "description": "Speed and proven synergy. Leverages existing collaboration patterns.",
      "strategy_preference": "speed",
      "color": "#FF9800"
    }
  ]
}
```

**Status Codes:**
- `200 OK`: Success

---

## Admin Endpoints

### POST /admin/recompute-skills

Recalculate skill levels for all employees.

**Response:**
```json
{
  "ok": true,
  "result": {
    "updated": 150,
    "message": "Recomputed skill levels for 150 relationships"
  }
}
```

**Status Codes:**
- `200 OK`: Success
- `500 Internal Server Error`: Server error

**Note:** This operation can be slow for large datasets. Consider running during off-peak hours.

---

### POST /admin/normalize

Re-normalize all employee UIDs in the graph.

**Response:**
```json
{
  "ok": true,
  "result": {
    "updated": 0,
    "message": "Not implemented yet"
  }
}
```

**Status Codes:**
- `200 OK`: Success
- `500 Internal Server Error`: Server error

**Warning:** This is a destructive operation. Backup database before running.

---

## Query Endpoints

### GET /employees

List all employees in the system.

**Response:**
```json
{
  "employees": [
    {
      "id": "emp_a1b2c3d4e5f6g7h8",
      "nombre": "Juan Pérez",
      "rol": "Senior Developer"
    },
    {
      "id": "emp_x9y8z7w6v5u4t3s2",
      "nombre": "María García",
      "rol": "Tech Lead"
    }
  ]
}
```

**Status Codes:**
- `200 OK`: Success
- `500 Internal Server Error`: Server error

**Note:** If `HASH_ACTOR_IDS=true`, IDs will be hashed (e.g., `emp_a1b2c3...`).

---

## Error Codes

### Standard HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 400 | Bad Request | Invalid parameters or malformed request |
| 404 | Not Found | Endpoint not found |
| 500 | Internal Server Error | Server-side error |

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

---

## Rate Limiting

Currently, no rate limiting is implemented. For production, consider:
- Rate limiting on `/admin/*` endpoints
- Caching for `/api/mission-profiles` and `/api/linchpins`

---

## Examples

### cURL Examples

**Get team recommendations:**
```bash
curl -X POST http://localhost:8000/api/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "requisitos_hard": {"skills": ["Python", "Docker"]},
    "k": 5,
    "mission_profile": "entrega_rapida"
  }'
```

**Get linchpins:**
```bash
curl http://localhost:8000/api/linchpins
```

**Recompute skills:**
```bash
curl -X POST http://localhost:8000/admin/recompute-skills
```

### Python Examples

```python
import requests

# Get team recommendations
response = requests.post('http://localhost:8000/api/recommend', json={
    "requisitos_hard": {"skills": ["Python", "Docker"]},
    "k": 5,
    "mission_profile": "innovacion",
    "week": "2025-W01",
    "min_hours": 25
})

dossiers = response.json()['dossiers']
for dossier in dossiers:
    print(f"{dossier['title']}: {dossier['executive_summary']['recommendation']}")
```

---

## Postman Collection

Import the included `postman_collection.json` for pre-configured requests with examples.

---

**Last Updated:** 2024-11-24  
**Maintained by:** Santiago Palma (spalmaa@unsa.edu.pe)
