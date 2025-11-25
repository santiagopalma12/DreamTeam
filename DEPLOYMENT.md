# Deployment Guide - Project Chimera

## Prerequisites

### Required Software
- **Python:** 3.9 or higher
- **Neo4j:** 4.4 or higher
- **Git:** For cloning repository
- **pip:** Python package manager

### Optional
- **Docker:** For containerized Neo4j
- **Postman:** For API testing

---

## Installation Steps

### 1. Install Neo4j

#### Option A: Docker (Recommended)
```bash
docker run \
  --name neo4j-chimera \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/neo4jpasswd \
  -v $HOME/neo4j/data:/data \
  neo4j:latest
```

Access Neo4j Browser: http://localhost:7474

#### Option B: Local Installation
1. Download from https://neo4j.com/download/
2. Install and start Neo4j
3. Set password via Neo4j Browser

---

### 2. Clone Repository

```bash
git clone https://github.com/santiagopalma12/DreamTeam.git
cd DreamTeam
```

---

### 3. Install Python Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
```

**Required packages:**
- fastapi
- uvicorn
- neo4j
- pydantic
- pydantic-settings
- requests
- pyyaml
- networkx

---

### 4. Configure Environment Variables

Create `.env` file in project root:

```bash
cp .env.example .env
```

Edit `.env`:

```bash
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASS=neo4jpasswd

# GitHub Integration
GITHUB_TOKEN=your_github_personal_access_token

# Jira Integration (Optional)
JIRA_BASE=https://your-domain.atlassian.net
JIRA_USER=your_email@example.com
JIRA_TOKEN=your_jira_api_token

# Privacy Configuration
HASH_ACTOR_IDS=false  # Set to 'true' in production
PRIVACY_SALT=change_me_in_production_please_use_strong_random_string
```

**Important:** 
- Generate GitHub token at: https://github.com/settings/tokens
- For Jira token: https://id.atlassian.com/manage-profile/security/api-tokens

---

### 5. Initialize Database

#### Apply Neo4j Schema
```bash
python scripts/apply_schema.py
```

This creates:
- Unique constraints (Empleado, Skill, Evidence)
- Indexes for performance
- ManualConstraint support

#### Seed Skill Taxonomy
```bash
python scripts/seed_taxonomy.py
```

This loads initial skill taxonomy from `backend/neo4j/taxonomy.csv`.

---

### 6. Run Ingestion (Optional)

#### GitHub Ingestion
```bash
cd backend
python -m app.ingestors.run_ingest github
```

#### Jira Ingestion
```bash
python -m app.ingestors.run_ingest jira
```

#### Availability Ingestion
```bash
# Edit backend/app/ingestors/availability.csv first
python -m app.ingestors.run_ingest availability
```

---

### 7. Start API Server

```bash
cd backend
uvicorn app.main:app --reload
```

Server will start at: http://localhost:8000

**API Documentation:** http://localhost:8000/docs (Swagger UI)

---

## Verification

### Test API Endpoints

```bash
# Health check
curl http://localhost:8000/employees

# Get mission profiles
curl http://localhost:8000/api/mission-profiles

# Get team recommendations
curl -X POST http://localhost:8000/api/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "requisitos_hard": {"skills": ["Python"]},
    "k": 5
  }'
```

### Check Neo4j Data

Open Neo4j Browser (http://localhost:7474) and run:

```cypher
// Count employees
MATCH (e:Empleado) RETURN count(e)

// Count skills
MATCH (s:Skill) RETURN count(s)

// Count evidence
MATCH (ev:Evidence) RETURN count(ev)

// View sample data
MATCH (e:Empleado)-[r:DEMUESTRA_COMPETENCIA]->(s:Skill)
RETURN e.id, s.name, r.nivel
LIMIT 10
```

---

## Production Deployment

### Security Checklist

- [ ] Change `PRIVACY_SALT` to strong random string
- [ ] Set `HASH_ACTOR_IDS=true` for PII protection
- [ ] Use environment variables (not `.env` file)
- [ ] Enable Neo4j authentication
- [ ] Implement API authentication (OAuth2/API Keys)
- [ ] Enable HTTPS
- [ ] Configure CORS properly
- [ ] Set up rate limiting

### Environment Variables (Production)

```bash
# Use secrets manager (AWS Secrets Manager, Azure Key Vault, etc.)
export NEO4J_URI=bolt://production-neo4j:7687
export NEO4J_USER=production_user
export NEO4J_PASS=strong_password_here
export PRIVACY_SALT=very_strong_random_salt_min_32_chars
export HASH_ACTOR_IDS=true
```

### Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:

```bash
docker build -t chimera-api .
docker run -p 8000:8000 --env-file .env chimera-api
```

### Docker Compose (Full Stack)

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  neo4j:
    image: neo4j:latest
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      NEO4J_AUTH: neo4j/production_password
    volumes:
      - neo4j_data:/data

  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      NEO4J_URI: bolt://neo4j:7687
      NEO4J_USER: neo4j
      NEO4J_PASS: production_password
      HASH_ACTOR_IDS: "true"
      PRIVACY_SALT: ${PRIVACY_SALT}
    depends_on:
      - neo4j

volumes:
  neo4j_data:
```

Run:

```bash
docker-compose up -d
```

---

## Troubleshooting

### Issue: Cannot connect to Neo4j

**Solution:**
```bash
# Check Neo4j is running
docker ps | grep neo4j

# Check connection
curl http://localhost:7474

# Verify credentials in .env
```

### Issue: Import errors (pydantic, etc.)

**Solution:**
```bash
# Reinstall dependencies
pip install --upgrade -r backend/requirements.txt

# Check Python version
python --version  # Should be 3.9+
```

### Issue: GitHub ingestion fails

**Solution:**
```bash
# Verify token has correct permissions
# Required scopes: repo, read:org

# Test token
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user
```

### Issue: Slow performance

**Solution:**
```bash
# Verify indexes are created
# In Neo4j Browser:
CALL db.indexes()

# Recompute skills in batches
# (Not implemented yet - manual batching required)
```

---

## Monitoring

### Logs

```bash
# API logs
uvicorn app.main:app --log-level info

# Neo4j logs
docker logs neo4j-chimera
```

### Metrics

Consider implementing:
- Prometheus for metrics
- Grafana for dashboards
- ELK stack for log aggregation

---

## Backup & Recovery

### Neo4j Backup

```bash
# Stop Neo4j
docker stop neo4j-chimera

# Backup data directory
tar -czf neo4j-backup-$(date +%Y%m%d).tar.gz $HOME/neo4j/data

# Restart Neo4j
docker start neo4j-chimera
```

### Restore

```bash
# Stop Neo4j
docker stop neo4j-chimera

# Restore data
tar -xzf neo4j-backup-YYYYMMDD.tar.gz -C $HOME/neo4j/

# Restart Neo4j
docker start neo4j-chimera
```

---

## Scaling Considerations

### Horizontal Scaling
- Use Neo4j Causal Cluster for read replicas
- Load balance API with Nginx/HAProxy
- Consider caching layer (Redis)

### Vertical Scaling
- Increase Neo4j heap size
- Optimize Cypher queries
- Add database indexes

---

## Support

**Issues:** https://github.com/santiagopalma12/DreamTeam/issues  
**Email:** spalmaa@unsa.edu.pe  
**Documentation:** See README.md and API_DOCUMENTATION.md

---

**Last Updated:** 2024-11-24  
**Maintained by:** Santiago Palma
