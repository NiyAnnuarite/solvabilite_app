// Graphiques interactifs pour Solvabilité II
class SolvabiliteCharts {
    constructor() {
        this.colors = {
            primary: '#3498db',
            success: '#2ecc71',
            warning: '#f39c12',
            danger: '#e74c3c',
            info: '#17a2b8',
            secondary: '#95a5a6',
            tier1: '#27ae60',
            tier2: '#f39c12',
            tier3: '#e74c3c'
        };
    }

    initChartSCRBreakdown(canvasId, data) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        return new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['SCR Marché', 'SCR Crédit', 'SCR Vie', 'SCR Non-Vie', 'SCR Opérationnel'],
                datasets: [{
                    data: data.values,
                    backgroundColor: [
                        this.colors.primary,
                        this.colors.success,
                        this.colors.warning,
                        this.colors.info,
                        this.colors.secondary
                    ],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                    },
                    title: {
                        display: true,
                        text: 'Répartition du SCR par Module'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = Math.round((value / total) * 100);
                                return `${label}: ${value.toLocaleString('fr-FR')} € (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }

    initChartEvolutionRatio(canvasId, data) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        return new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.dates,
                datasets: [
                    {
                        label: 'Ratio SCR',
                        data: data.ratiosSCR,
                        borderColor: this.colors.primary,
                        backgroundColor: this.colors.primary + '20',
                        tension: 0.4,
                        fill: true,
                        borderWidth: 2
                    },
                    {
                        label: 'Ratio MCR',
                        data: data.ratiosMCR,
                        borderColor: this.colors.success,
                        backgroundColor: this.colors.success + '20',
                        tension: 0.4,
                        fill: true,
                        borderWidth: 2
                    },
                    {
                        label: 'Seuil Minimum',
                        data: Array(data.dates.length).fill(100),
                        borderColor: this.colors.danger,
                        borderDash: [5, 5],
                        borderWidth: 1,
                        fill: false,
                        pointRadius: 0
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Évolution des Ratios de Solvabilité'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: function(context) {
                                return `${context.dataset.label}: ${context.parsed.y.toFixed(1)}%`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        title: {
                            display: true,
                            text: 'Ratio (%)'
                        },
                        min: 80
                    }
                }
            }
        });
    }

    initChartFondsPropres(canvasId, data) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Tier 1', 'Tier 2', 'Tier 3'],
                datasets: [{
                    label: 'Fonds Propres (€)',
                    data: data,
                    backgroundColor: [
                        this.colors.tier1,
                        this.colors.tier2,
                        this.colors.tier3
                    ],
                    borderColor: [
                        this.colors.tier1,
                        this.colors.tier2,
                        this.colors.tier3
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Répartition des Fonds Propres par Tier'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `Montant: ${context.parsed.y.toLocaleString('fr-FR')} €`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return value.toLocaleString('fr-FR') + ' €';
                            }
                        }
                    }
                }
            }
        });
    }
}

// Initialisation automatique des graphiques
document.addEventListener('DOMContentLoaded', function() {
    if (typeof chartData !== 'undefined') {
        const charts = new SolvabiliteCharts();

        if (chartData.scrBreakdown) {
            charts.initChartSCRBreakdown('scrBreakdownChart', chartData.scrBreakdown);
        }

        if (chartData.evolution) {
            charts.initChartEvolutionRatio('evolutionChart', chartData.evolution);
        }

        if (chartData.fondsPropres) {
            charts.initChartFondsPropres('fondsPropresChart', chartData.fondsPropres);
        }
    }
});

// Export pour utilisation globale
window.SolvabiliteCharts = SolvabiliteCharts;