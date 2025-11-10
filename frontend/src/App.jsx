import React, { useState } from 'react';
import GraphView from './components/GraphView';
import DossierPanel from './components/DossierPanel';
import { proposeTeam } from './components/api.js';
import { Button, Box, Typography } from '@mui/material';


export default function App() {
const [dossier, setDossier] = useState(null);


const handleGenerate = async () => {
	// Construye el payload que espera el backend (TeamRequest)
	const payload = {
		requisitos_hard: { skill_python: 1, skill_git: 1 },
		perfil_mision: 'mantenimiento',
		k: 3,
		preferences: {},
	};

	try {
		const res = await proposeTeam(payload);
		// FastAPI devuelve { proposals: [...] } según main.py, así que usamos res.proposals
			const proposals = res.proposals ?? res;
			// Normalize the response: backend returns { proposals: [...] }
			const first = Array.isArray(proposals) ? proposals[0] : proposals;
			const normalized = {
				title: first?.mode ?? 'Propuesta',
				metrics: first?.metrics ?? {},
				riesgos: first?.riesgos ?? [],
				members: first?.members ?? [],
			};
			setDossier(normalized);
	} catch (err) {
		// Muestra el error de validación (422) con detalle si está disponible
		console.error('Error al pedir propuesta de equipo', err);
		if (err?.response?.data) console.error('Detalle backend:', err.response.data);
	}
};


return (
<Box sx={{ display: 'flex', gap: 3, p: 3 }}>
<Box sx={{ flex: 2 }}>
<Typography variant="h5" gutterBottom>Grafo de Colaboración</Typography>
<GraphView dossier={dossier} />
<Button variant="contained" color="primary" onClick={handleGenerate}>Generar Equipo</Button>
</Box>
<Box sx={{ flex: 1 }}>
{dossier && <DossierPanel dossier={dossier} />}
</Box>
</Box>
);
}