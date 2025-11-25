# Project Chimera - Guía de Presentación para Feria

**Autor:** Santiago Palma  
**Email:** spalmaa@unsa.edu.pe  
**Universidad:** Universidad Nacional de San Agustín de Arequipa

---

## 🎯 Elevator Pitch (30 segundos)

> "Project Chimera es un sistema inteligente que arma equipos de trabajo basándose en evidencia real, no en encuestas. Analiza commits de GitHub, tickets de Jira y disponibilidad para recomendar la mejor combinación de personas según la misión del proyecto. Es como tener un asesor de RRHH que conoce el trabajo real de cada persona."

---

## 📊 Problema que Resuelve

### El Problema Tradicional:
❌ Matrices de habilidades basadas en auto-evaluación  
❌ Sesgos en selección de equipos  
❌ No considera colaboración previa  
❌ Ignora disponibilidad real  
❌ No identifica riesgos (Bus Factor)

### La Solución Chimera:
✅ **Evidencia objetiva** de GitHub, Jira, etc.  
✅ **Scoring contextual** con decay temporal  
✅ **3 estrategias** según misión del proyecto  
✅ **Detección de linchpins** (empleados críticos)  
✅ **Cumple GDPR** con hashing de PII

---

## 🏗️ Arquitectura (Explicación Simple)

```
Datos Reales          Análisis              Recomendaciones
─────────────         ────────             ─────────────────
GitHub Commits   →                    →   "Safe Bet Team"
Jira Tickets     →   Neo4j Graph     →   "Growth Team"
Disponibilidad   →   + Guardian      →   "Speed Squad"
                     + Scoring
```

**Componentes Clave:**
1. **Conectores** - Extraen datos de GitHub, Jira, CSV
2. **Grafo Neo4j** - Almacena relaciones (quién trabajó con quién)
3. **Motor de Scoring** - Calcula nivel de habilidad con decay temporal
4. **Guardian** - Asesor que genera 3 opciones de equipo
5. **Detector de Linchpins** - Identifica empleados críticos (Bus Factor)

---

## 🎬 Demo Script (5 minutos)

### 1. Contexto (30 seg)
"Imaginen que necesitan armar un equipo de 5 personas para un proyecto urgente de DevOps. Necesitan Python, Docker y Kubernetes."

### 2. Mostrar Datos (1 min)
**Neo4j Browser:**
```cypher
// Mostrar empleados y habilidades
MATCH (e:Empleado)-[r:DEMUESTRA_COMPETENCIA]->(s:Skill)
WHERE s.name IN ['Python', 'Docker', 'Kubernetes']
RETURN e.id, s.name, r.nivel
LIMIT 10
```

"Estos datos vienen de commits reales de GitHub, no de encuestas."

### 3. Llamar API (2 min)
**Postman o cURL:**
```bash
curl -X POST http://localhost:8000/api/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "requisitos_hard": {"skills": ["Python", "Docker", "Kubernetes"]},
    "k": 5,
    "mission_profile": "entrega_rapida"
  }'
```

**Mostrar resultado:**
- 3 dossiers diferentes
- Executive summary (Pros/Cons)
- Recomendación (APPROVE/REVIEW/REJECT)

### 4. Mostrar Linchpins (1 min)
```bash
curl http://localhost:8000/api/linchpins
```

"Estos son empleados críticos. Si se van, el proyecto está en riesgo. El sistema recomienda hacer knowledge transfer."

### 5. Explicar Privacidad (30 seg)
"En producción, todos los IDs se hashean con SHA-256. Cumple GDPR. El grafo no almacena nombres reales, solo hashes."

---

## 💡 Características Destacables

### 1. Scoring Contextual
**No es un simple promedio:**
- **Decay temporal:** Habilidades antiguas valen menos
- **Impact weighting:** Commits en archivos críticos valen más
- **Hoarding penalty:** Fomenta validación por pares

**Ejemplo:**
```
Commit en archivo crítico (main.py) hace 30 días:
  Base: 3.0
  × Impact (High): 1.5
  × Decay (30 días): 1.0
  = Score: 4.5

Commit en archivo trivial (README.md) hace 200 días:
  Base: 3.0
  × Impact (Low): 0.7
  × Decay (200 días): 0.5
  = Score: 1.05
```

### 2. Guardian (3 Estrategias)
**Safe Bet:** Alta habilidad + alta disponibilidad  
**Growth Team:** Mix senior/junior para mentoría  
**Speed Squad:** Historial de colaboración probado

### 3. Mission Profiles
**Mantenimiento:** Prioriza estabilidad (skill × 1.5)  
**Innovación:** Fomenta experimentación (colaboración × 1.2)  
**Entrega Rápida:** Maximiza velocidad (disponibilidad × 1.5)

### 4. Detección de Linchpins
**Algoritmo:**
- Betweenness centrality (teoría de grafos)
- Unique skill detection
- Risk levels: CRITICAL/HIGH/MEDIUM/LOW

### 5. Privacy by Design
- SHA-256 hashing con salt
- Cross-source UID normalization
- Cumple GDPR Article 5(1)(f) y Article 25

---

## 📈 Casos de Uso

### Caso 1: Startup Tech
**Problema:** Equipo pequeño, necesitan maximizar productividad  
**Solución:** Mission profile "entrega_rapida" + detección de linchpins  
**Resultado:** Equipos balanceados, identifican riesgos de Bus Factor

### Caso 2: Empresa Grande
**Problema:** Silos de conocimiento, falta colaboración  
**Solución:** Mission profile "innovacion" + Growth Team strategy  
**Resultado:** Equipos cross-funcionales, knowledge transfer

### Caso 3: Proyecto Crítico
**Problema:** Sistema legacy, necesitan estabilidad  
**Solución:** Mission profile "mantenimiento" + Safe Bet strategy  
**Resultado:** Equipo senior con experiencia probada

---

## 🎓 Tecnologías Utilizadas

**Backend:**
- Python 3.9+ (FastAPI, Pydantic)
- Neo4j 4.4+ (Graph Database)
- NetworkX (Centrality algorithms)

**Integraciones:**
- GitHub API (commits, PRs, reviews)
- Jira API (tickets, story points)
- CSV (availability data)

**Seguridad:**
- SHA-256 hashing
- Environment variables
- GDPR compliance

---

## 🚀 Roadmap Completado

✅ Phase 0: Foundation & Schema  
✅ Phase 1: Graph & Taxonomy  
✅ Phase 2: Multi-Source Ingestion  
✅ Phase 3: Privacy & Normalization  
✅ Phase 4: Contextual Scoring  
✅ Phase 5: Guardian Co-Pilot  
✅ Phase 6: Policy & Governance  
⏳ Phase 7: Dossier Views (Pendiente)  
⏳ Phase 8: Frontend UI (Pendiente)

**Estado Actual:** Backend MVP 100% funcional

---

## 🎤 Preguntas Frecuentes

### ¿Cómo maneja la privacidad?
"Todos los IDs de empleados se hashean con SHA-256 antes de entrar al grafo. En producción, nadie puede ver nombres reales, solo hashes. Cumple GDPR."

### ¿Qué pasa si alguien no tiene GitHub?
"El sistema es multi-fuente. Puede usar Jira, Slack, o cualquier fuente de evidencia. GitHub es solo un ejemplo."

### ¿Cómo sabe qué habilidades tiene cada persona?
"Analiza los archivos que modifica. Si edita archivos Python, infiere habilidad en Python. Si edita Dockerfiles, infiere Docker. No es auto-reporte."

### ¿Y si dos personas no se llevan bien?
"Hay un mecanismo de `MANUAL_CONSTRAINT`. RRHH puede marcar pares que no deben trabajar juntos. El Guardian lo respeta."

### ¿Qué es el Bus Factor?
"Si una persona se va de vacaciones (o renuncia), ¿el proyecto se detiene? Eso es Bus Factor. El sistema detecta empleados críticos y recomienda knowledge transfer."

### ¿Puedo forzar a alguien en un equipo?
"Sí, con `force_include`. O excluir con `force_exclude`. El sistema respeta overrides de managers."

---

## 📸 Capturas Recomendadas

1. **Neo4j Browser:** Grafo de empleados y habilidades
2. **Postman:** Request/Response de `/api/recommend`
3. **JSON Response:** Executive summary con Pros/Cons
4. **Linchpins:** Lista de empleados críticos
5. **Mission Profiles:** Comparación de pesos

---

## 🏆 Diferenciadores Clave

**vs. LinkedIn Skills:**  
❌ LinkedIn: Auto-reporte  
✅ Chimera: Evidencia objetiva

**vs. Matrices de Habilidades:**  
❌ Matrices: Estáticas  
✅ Chimera: Decay temporal

**vs. Asignación Manual:**  
❌ Manual: Sesgos  
✅ Chimera: Data-driven

**vs. Otros Sistemas:**  
❌ Otros: No consideran disponibilidad  
✅ Chimera: Hard constraint de horas

---

## 🎯 Mensaje Final

> "Project Chimera transforma la formación de equipos de un arte subjetivo a una ciencia basada en datos. No reemplaza a los managers, los asiste con evidencia objetiva para tomar mejores decisiones."

---

## 📞 Contacto

**Santiago Palma**  
📧 spalmaa@unsa.edu.pe  
🐙 [@santiagopalma12](https://github.com/santiagopalma12)  
🏛️ Universidad Nacional de San Agustín de Arequipa

**Repositorio:** https://github.com/santiagopalma12/DreamTeam

---

**¡Gracias por su atención!**
