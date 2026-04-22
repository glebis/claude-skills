# Chart Library

Chart.js patterns for Tufte reports. All use Chart.js 4.x via CDN.

## CDN and Defaults

```html
<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
```

```javascript
// Tufte defaults — set BEFORE creating any charts
Chart.defaults.font.family = "'EB Garamond', Georgia, serif";
Chart.defaults.font.size = 13;
Chart.defaults.color = '#555';
Chart.defaults.plugins.legend.labels.usePointStyle = false;
Chart.defaults.plugins.legend.labels.boxWidth = 8;
Chart.defaults.plugins.legend.labels.boxHeight = 8;
Chart.defaults.plugins.legend.labels.borderRadius = 4;
Chart.defaults.plugins.legend.labels.font = { family: "'EB Garamond', serif", size: 11 };
Chart.defaults.plugins.legend.labels.padding = 14;
Chart.defaults.plugins.tooltip.backgroundColor = '#1a1a1a';
Chart.defaults.plugins.tooltip.cornerRadius = 2;
Chart.defaults.plugins.tooltip.padding = 10;
Chart.defaults.scale.grid.color = '#eee';
Chart.defaults.animation = {
  duration: 800,
  easing: 'easeOutQuart',
  delay: (ctx) => ctx.type === 'data' ? ctx.dataIndex * 8 : 0
};

// Solid filled legend dots (override default hollow circles for line charts)
const defaultGen = Chart.defaults.plugins.legend.labels.generateLabels;
Chart.defaults.plugins.legend.labels.generateLabels = function(chart) {
  const items = defaultGen.call(this, chart);
  items.forEach(item => {
    const ds = chart.data.datasets[item.datasetIndex];
    const color = ds.borderColor || ds.backgroundColor;
    item.fillStyle = Array.isArray(color) ? color[0] : color;
    item.strokeStyle = 'transparent';
    item.lineWidth = 0;
    item.borderRadius = 4;
  });
  return items;
};
```

## Pattern 1: Bar + Line (Dual Axis)

Best for: comparing volume (bars) with a rate/trend (line) on different scales.

```javascript
new Chart(document.getElementById('myChart'), {
  type: 'bar',
  data: {
    labels: data.map(d => formatDate(d.date)),
    datasets: [
      {
        label: 'Volume',
        data: data.map(d => d.volume),
        backgroundColor: 'rgba(196,90,40,0.25)',
        borderWidth: 0,
        borderRadius: 1,
        order: 2
      },
      {
        label: 'Rate',
        data: data.map(d => d.rate),
        type: 'line',
        borderColor: 'rgba(42,80,140,0.7)',
        backgroundColor: 'rgba(42,80,140,0.06)',
        fill: true,
        borderWidth: 1.5,
        pointRadius: 0,
        pointHitRadius: 8,
        tension: 0.3,
        yAxisID: 'y1',
        order: 1
      }
    ]
  },
  options: {
    responsive: true,
    interaction: { mode: 'index', intersect: false },
    scales: {
      x: { grid: { display: false }, ticks: { maxTicksLimit: 12, font: { size: 11 } } },
      y: { position: 'left', title: { display: true, text: 'Volume' } },
      y1: { position: 'right', title: { display: true, text: 'Rate' }, grid: { display: false } }
    },
    plugins: { legend: { position: 'top', align: 'end' } }
  }
});
```

## Pattern 2: SPC Control Chart

Best for: monitoring a metric against statistical control limits.

```javascript
new Chart(document.getElementById('spcChart'), {
  type: 'line',
  data: {
    labels: weekLabels,
    datasets: [
      {
        label: 'Metric',
        data: weeklyValues,
        borderColor: 'rgba(42,122,90,0.8)',
        backgroundColor: weeklyValues.map(v => v < centerline ? 'rgba(160,42,42,0.6)' : 'rgba(42,122,90,0.6)'),
        pointBackgroundColor: weeklyValues.map(v => v < centerline ? 'rgba(160,42,42,0.6)' : 'rgba(42,122,90,0.6)'),
        borderWidth: 1.5,
        pointRadius: 4,
        tension: 0.2,
        fill: false
      },
      {
        label: 'Centerline',
        data: Array(weekLabels.length).fill(centerline),
        borderColor: 'rgba(0,0,0,0.2)',
        borderDash: [6, 4],
        borderWidth: 1,
        pointRadius: 0,
        fill: false
      },
      {
        label: 'Lower limit',
        data: Array(weekLabels.length).fill(lowerLimit),
        borderColor: 'rgba(160,42,42,0.3)',
        borderDash: [4, 4],
        borderWidth: 1,
        pointRadius: 0,
        fill: false
      }
    ]
  }
});
```

## Pattern 3: Multi-line Comparison (No Fill)

Best for: comparing 2-3 trends on the same scale.

```javascript
// Use distinct colors, no area fill, solid dots
// Use borderDash for the least important series
{
  label: 'Primary',
  borderColor: 'rgba(196,90,40,0.8)',
  pointBackgroundColor: 'rgba(196,90,40,0.8)',
  fill: false, borderWidth: 2, pointRadius: 3, tension: 0.3
},
{
  label: 'Secondary',
  borderColor: 'rgba(42,122,90,0.8)',
  pointBackgroundColor: 'rgba(42,122,90,0.8)',
  fill: false, borderWidth: 2, pointRadius: 3, tension: 0.3
},
{
  label: 'Tertiary',
  borderColor: 'rgba(90,90,170,0.7)',
  pointBackgroundColor: 'rgba(90,90,170,0.7)',
  fill: false, borderWidth: 1.5, pointRadius: 3, borderDash: [4, 3], tension: 0.3
}
```

## Pattern 4: Inline SVG Sparkline

Best for: word-sized trend indicators inside text or table cells.

```html
<svg class="spark-inline" id="sparkId" width="50" height="14"></svg>
```

```javascript
function drawSparkline(svgId, values, color) {
  const svg = document.getElementById(svgId);
  if (!svg) return;
  const w = parseInt(svg.getAttribute('width'));
  const h = parseInt(svg.getAttribute('height'));
  const pad = 2;
  const max = Math.max(...values);
  const min = Math.min(...values);
  const range = max - min || 1;
  const step = (w - pad * 2) / (values.length - 1);

  const points = values.map((v, i) => {
    const x = pad + i * step;
    const y = h - pad - ((v - min) / range) * (h - pad * 2);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });

  const areaPoints = [`${pad},${h-pad}`, ...points, `${(pad+(values.length-1)*step).toFixed(1)},${h-pad}`].join(' ');
  const lastX = pad + (values.length - 1) * step;
  const lastY = h - pad - ((values[values.length-1] - min) / range) * (h - pad * 2);

  svg.innerHTML = `
    <polygon points="${areaPoints}" fill="${color}" opacity="0.12" />
    <polyline points="${points.join(' ')}" fill="none" stroke="${color}" stroke-width="1.2" stroke-linejoin="round" />
    <circle cx="${lastX.toFixed(1)}" cy="${lastY.toFixed(1)}" r="2" fill="${color}" />
  `;
}
```

## Pattern 5: Strip Chart (Horizontal Bar Rows)

Best for: weekly/periodic data with sparse annotations. Tufte-style alternative to bar charts.

Generated via JS — creates rows with `.tg-week` (label) + `.tg-count` (number) + `.tg-bar-area` (proportional bar) + `.tg-note` (annotation).

See components.md for the full CSS.

## Pattern 6: Stacked Bar (Language/Category Split)

```javascript
{
  label: 'Category A',
  data: data.map(d => d.catA),
  backgroundColor: 'rgba(42,122,90,0.55)',
  borderColor: 'rgba(42,122,90,0.7)',
  borderWidth: 0.5,
  borderRadius: 1
},
{
  label: 'Category B',
  data: data.map(d => d.catB),
  backgroundColor: 'rgba(204,140,0,0.65)',
  borderColor: 'rgba(180,120,0,0.8)',
  borderWidth: 0.5,
  borderRadius: 1
}
// scales: { x: { stacked: true }, y: { stacked: true } }
```

## Anti-Patterns (Don't Do This)

- Don't use `Chart.defaults.scale.grid = { ... }` — it replaces the entire object. Set `.color` individually
- Don't use `usePointStyle: true` for circles — it creates ovals. Use `boxWidth/boxHeight` with `borderRadius`
- Don't use `@4.4.7` or specific patch versions in CDN — they may not exist. Use `@4`
- Don't put two charts back-to-back without narrative/table separation
- Don't use more than 2 y-axes on a single chart
- Don't use area fills on multi-line comparison charts (creates visual mud)
