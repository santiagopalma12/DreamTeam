import React from 'react';
import { Box, Typography, Paper, Divider } from '@mui/material';


export default function DossierPanel({ dossier }) {
	// defensive defaults in case backend returns partial data
	const { title = 'Propuesta', metrics = {}, riesgos = [], members = [] } = dossier || {};

	// build member name lookup
	const memberMap = {};
	if (Array.isArray(members)) {
		members.forEach(m => {
			if (typeof m === 'string') memberMap[m] = m;
			else memberMap[m.id] = m.nombre || m.id;
		});
	}

	return (
		<Paper sx={{ p: 2, maxHeight: '90vh', overflow: 'auto' }}>
			<Typography variant="h6">{title}</Typography>
			<Divider sx={{ my: 2 }} />

			<Typography variant="subtitle1">📊 Métricas</Typography>
			<pre>{JSON.stringify(metrics, null, 2)}</pre>

			<Typography variant="subtitle1">⚠️ Riesgos</Typography>
			<ul>
				{Array.isArray(riesgos) && riesgos.length > 0 ? (
					riesgos.map((r, i) => (
						<li key={i}>{r.tipo}: {r.nivel} — {r.descripcion}</li>
					))
				) : (
					<li>No hay riesgos identificados</li>
				)}
			</ul>

			<Typography variant="subtitle1">👥 Miembros</Typography>
					<ul>
						{Array.isArray(members) && members.length > 0 ? (
							members.map((m, i) => {
								// members can be either an object {id,nombre,rol} or just an id string
								const id = typeof m === 'string' ? m : (m.id ?? m.nombre ?? 'unknown');
								const nombre = typeof m === 'string' ? m : (m.nombre ?? m.id ?? m);
								const rol = typeof m === 'string' ? '—' : (m.rol ?? '—');
								return (
									<li key={i}><b>{nombre}</b> — {rol} <small style={{color:'#666', marginLeft:8}}>({id})</small></li>
								);
							})
						) : (
							<li>No hay miembros propuestos</li>
						)}
					</ul>

				<Typography variant="subtitle1" sx={{mt:2}}>🧾 Justificaciones (evidencias)</Typography>
				{Array.isArray(dossier.justificaciones) && dossier.justificaciones.length > 0 ? (
					<div>
						{dossier.justificaciones.map((j, idx) => (
							<Paper key={idx} sx={{p:1, mb:1}} variant="outlined">
								<Typography variant="subtitle2">{memberMap[j.id] || j.id}</Typography>
								{Array.isArray(j.skills) && j.skills.length > 0 ? (
									<ul>
										{j.skills.map((sk, sidx) => (
											<li key={sidx}>
												<b>{sk.skill}</b> — nivel {sk.nivel?.toFixed ? sk.nivel.toFixed(2) : sk.nivel}
												{Array.isArray(sk.evidencias) && sk.evidencias.length > 0 ? (
													<ul>
														{sk.evidencias.map((ev, eidx) => (
															<li key={eidx}>
																{ev.date ? <small>{ev.date} — </small> : null}
																{ev.actor ? <small>{ev.actor} — </small> : null}
																{ev.url ? (
																	<a href={ev.url} target="_blank" rel="noreferrer">{ev.url}</a>
																) : <span>{ev.raw}</span>}
															</li>
														))}
													</ul>
												) : <div style={{color:'#666'}}>Sin evidencias</div>}
										</li>
									))}
									</ul>
								) : <div style={{color:'#666'}}>No hay justificaciones para este miembro</div>}
							</Paper>
						))}
					</div>
				) : (
					<div style={{color:'#666'}}>No hay justificaciones disponibles</div>
				)}
		</Paper>
	);
}