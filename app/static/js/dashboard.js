// Dashboard — loads data from API and renders charts

async function loadDashboard() {
    try {
        const [summary, aging, revenue] = await Promise.all([
            fetch('/api/dashboard/summary').then(r => r.json()),
            fetch('/api/dashboard/aging').then(r => r.json()),
            fetch('/api/dashboard/revenue-monthly').then(r => r.json()),
        ]);

        // Summary cards
        document.getElementById('total-ar').textContent = '$' + (summary.total_ar || 0).toLocaleString();
        document.getElementById('invoices-month').textContent = summary.invoices_this_month || 0;
        document.getElementById('overdue-count').textContent = summary.overdue_count || 0;
        document.getElementById('revenue-mtd').textContent = '$' + (summary.revenue_mtd || 0).toLocaleString();

        // Aging chart
        new Chart(document.getElementById('aging-chart'), {
            type: 'bar',
            data: {
                labels: ['0-30 days', '31-60 days', '61-90 days', '90+ days'],
                datasets: [{
                    label: 'Outstanding ($)',
                    data: [aging.bucket_0_30 || 0, aging.bucket_31_60 || 0, aging.bucket_61_90 || 0, aging.bucket_90_plus || 0],
                    backgroundColor: ['#4caf50', '#ff9800', '#f44336', '#b71c1c'],
                }]
            },
            options: { indexAxis: 'y', responsive: true, plugins: { legend: { display: false } } }
        });

        // Revenue chart
        new Chart(document.getElementById('revenue-chart'), {
            type: 'line',
            data: {
                labels: (revenue.months || []),
                datasets: [{
                    label: 'Revenue ($)',
                    data: (revenue.amounts || []),
                    borderColor: '#1976d2',
                    fill: false,
                    tension: 0.3,
                }]
            },
            options: { responsive: true }
        });

    } catch (e) {
        console.log('Dashboard API not ready yet:', e);
    }

    // Load recent activity
    try {
        const resp = await fetch('/api/dashboard/recent-activity');
        const data = await resp.json();
        const tbody = document.getElementById('activity-table');
        if (data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5">No recent activity</td></tr>';
        } else {
            tbody.innerHTML = data.map(row =>
                `<tr><td>${row.date}</td><td>${row.event}</td><td>${row.invoice_number || '-'}</td><td>${row.client_name || '-'}</td><td>${row.amount ? '$' + row.amount.toLocaleString() : '-'}</td></tr>`
            ).join('');
        }
    } catch (e) {
        console.log('Activity API not ready:', e);
    }
}

async function batchGenerate() {
    if (!confirm('Generate invoices for all unbilled shipments?')) return;
    const btn = event.target;
    btn.disabled = true;
    btn.textContent = 'Processing...';
    try {
        const resp = await fetch('/api/agent/generate-batch', { method: 'POST' });
        const data = await resp.json();
        alert(`Generated ${data.count} invoices`);
        location.reload();
    } catch (e) {
        alert('Error: ' + e.message);
    } finally {
        btn.disabled = false;
        btn.textContent = 'Generate All Pending';
    }
}

async function sendReminders() {
    if (!confirm('Send reminders for all overdue invoices?')) return;
    const btn = event.target;
    btn.disabled = true;
    btn.textContent = 'Sending...';
    try {
        const resp = await fetch('/api/agent/send-reminders', { method: 'POST' });
        const data = await resp.json();
        alert(`Sent ${data.count} reminders`);
        location.reload();
    } catch (e) {
        alert('Error: ' + e.message);
    } finally {
        btn.disabled = false;
        btn.textContent = 'Send Reminders';
    }
}

document.addEventListener('DOMContentLoaded', loadDashboard);
