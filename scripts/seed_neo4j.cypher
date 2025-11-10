// Sample data for Project Chimera
// Creates employees, skills, and collaboration relationships

// Remove previous sample data (safe for testing)
MATCH (n:Empleado) DETACH DELETE n;
MATCH (s:Skill) DETACH DELETE s;

// Create skills
CREATE (:Skill {name: 'python'}), (:Skill {name: 'git'}), (:Skill {name: 'react'});

// Create employees
CREATE (a:Empleado {id: 'emp-ana', nombre: 'Ana Pérez', acceso: ['internal'], zona: 'Norte'}),
       (b:Empleado {id: 'emp-david', nombre: 'David Ruiz', acceso: ['internal'], zona: 'Norte'}),
       (c:Empleado {id: 'emp-lucia', nombre: 'Lucía Gómez', acceso: ['external'], zona: 'Sur'});

// Link employees to skills (DEMUESTRA_COMPETENCIA)
MATCH (a:Empleado {id:'emp-ana'}), (p:Skill {name:'python'}), (g:Skill {name:'git'})
CREATE (a)-[:DEMUESTRA_COMPETENCIA {evidencias: ['commit1'], nivel: 0.9, ultimaDemostracion: date()}]->(p),
       (a)-[:DEMUESTRA_COMPETENCIA {evidencias: ['commit2'], nivel: 0.6, ultimaDemostracion: date()}]->(g);

MATCH (b:Empleado {id:'emp-david'}), (p:Skill {name:'python'}), (r:Skill {name:'react'})
CREATE (b)-[:DEMUESTRA_COMPETENCIA {evidencias: ['commit3'], nivel: 0.7, ultimaDemostracion: date()}]->(p),
       (b)-[:DEMUESTRA_COMPETENCIA {evidencias: ['commit4'], nivel: 0.8, ultimaDemostracion: date()}]->(r);

MATCH (c:Empleado {id:'emp-lucia'}), (g:Skill {name:'git'})
CREATE (c)-[:DEMUESTRA_COMPETENCIA {evidencias: ['commit5'], nivel: 0.85, ultimaDemostracion: date()}]->(g);

// Collaboration relations
MATCH (a:Empleado {id:'emp-ana'}), (b:Empleado {id:'emp-david'}), (c:Empleado {id:'emp-lucia'})
CREATE (a)-[:HA_COLABORADO_CON {proyectosComunes: ['proj-1'], interaccionesPositivas: 5, interaccionesConflictivas: 0, frecuencia: 10, recencia: 3}]->(b),
       (b)-[:HA_COLABORADO_CON {proyectosComunes: ['proj-1','proj-2'], interaccionesPositivas: 3, interaccionesConflictivas: 1, frecuencia: 7, recencia: 5}]->(c),
       (a)-[:HA_COLABORADO_CON {proyectosComunes: ['proj-3'], interaccionesPositivas: 2, interaccionesConflictivas: 0, frecuencia: 2, recencia: 20}]->(c);

RETURN 'seeded' AS result;