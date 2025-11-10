import React, { useEffect, useRef, useState } from 'react';
import cytoscape from 'cytoscape';
import { getEmployees } from './api.js';


export default function GraphView({ dossier }) {
	const ref = useRef();
	const cyRef = useRef(null);
	const [initialNodesLoaded, setInitialNodesLoaded] = useState(false);

	useEffect(() => {
		// init cytoscape
		cyRef.current = cytoscape({
			container: ref.current,
			elements: [],
			style: [
				{ selector: 'node', style: { 'label': 'data(label)', 'background-color': '#1976d2', 'color': '#fff', 'text-valign': 'center' } },
				{ selector: 'edge', style: { 'line-color': '#90caf9', 'width': 2 } }
			],
			layout: { name: 'circle' }
		});

		return () => {
			if (cyRef.current) cyRef.current.destroy();
			cyRef.current = null;
		};
	}, []);

	useEffect(() => {
		const cy = cyRef.current;
		if (!cy) return;

		const members = dossier?.members ?? [];
		const elements = [];

		if (Array.isArray(members) && members.length > 0) {
			// show proposal members
			members.forEach((m, idx) => {
				const id = typeof m === 'string' ? m : (m.id ?? m.nombre ?? `m${idx}`);
				const label = typeof m === 'string' ? m : (m.nombre ?? m.id ?? `Member ${idx+1}`);
				elements.push({ data: { id, label } });
				if (idx > 0) {
					const prev = members[idx-1];
					const prevId = typeof prev === 'string' ? prev : (prev.id ?? prev.nombre);
					elements.push({ data: { source: prevId, target: id } });
				}
			});

			// replace whatever was in the graph with the new proposal
			try {
				cy.elements().remove();
				cy.add(elements);
				const layout = cy.layout ? cy.layout({ name: 'circle' }) : null;
				if (layout && typeof layout.run === 'function') layout.run();
			} catch (e) {
				console.error('error rendering proposal members', e);
			}

		} else {
			// load all employees for initial view, but only if graph is empty
			if (cy.elements().length > 0) return; // already has nodes, keep them

			getEmployees().then(empList => {
				const cyNow = cyRef.current;
				if (!cyNow) return; // component unmounted or cy destroyed
				const els = empList.map((e, i) => ({ data: { id: e.id, label: e.nombre ?? e.id } }));
				try {
					// only add if still empty
					if (cyNow.elements().length === 0) {
						cyNow.add(els);
						const layout = cyNow.layout ? cyNow.layout({ name: 'circle' }) : null;
						if (layout && typeof layout.run === 'function') layout.run();
						setInitialNodesLoaded(true);
					}
				} catch (e) {
					console.error('error adding initial employee nodes to cytoscape', e);
				}
			}).catch(err => {
				console.error('failed to load employees for initial graph', err);
			});
		}
	}, [dossier]);

	return <div ref={ref} style={{ width: '100%', height: '400px', border: '1px solid #ccc' }} />;
}