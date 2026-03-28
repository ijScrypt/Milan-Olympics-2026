function renderGraph(nodes, edges) {
    const container = document.getElementById('neo4j-graph-container');
    if (!container) return;

    const data = {
        nodes: new vis.DataSet(nodes),
        edges: new vis.DataSet(edges),
    };

    const options = {
        nodes: {
            shape: 'dot',
            size: 20,
            font: { size: 14, color: '#e5e5e5' },
            borderWidth: 2,
            shadow: true,
        },
        edges: {
            width: 2,
            font: { align: 'middle', size: 10, color: '#a3a3a3', strokeWidth: 3, strokeColor: '#09090b' },
            arrows: { to: { enabled: true, scaleFactor: 0.8 } },
            color: { color: '#52525b', highlight: '#6366f1', hover: '#a3a3a3' },
            smooth: { type: 'cubicBezier' },
            shadow: true,
        },
        physics: {
            forceAtlas2Based: {
                gravitationalConstant: -70,
                centralGravity: 0.01,
                springLength: 230,
                springConstant: 0.08,
            },
            minVelocity: 0.75,
            solver: 'forceAtlas2Based',
        },
        interaction: {
            hover: true,
            tooltipDelay: 200,
        },
        layout: {
            hierarchical: false,
        },
    };

    if (window.network) {
        window.network.destroy();
    }
    window.network = new vis.Network(container, data, options);
}

async function loadAndRenderGraph() {
    try {
        const graphData = await apiFetch('/graph');
        renderGraph(graphData.nodes, graphData.edges);
    } catch (error) {
        console.error('Failed to load and render graph:', error);
        showToast('Failed to load graph data', 'error');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const neo4jTab = document.getElementById('tab-neo4j');
    if (neo4jTab) {
        neo4jTab.addEventListener('click', () => {
            setTimeout(loadAndRenderGraph, 100);
        });
    }
});
