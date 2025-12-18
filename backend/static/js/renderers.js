import { store } from './store.js';
import { API_BASE } from './api.js';
import { formatCurrency, formatDate } from './utils.js';

// === Participants ===

export function renderParticipantCheckboxes() {
    const container = document.getElementById('participantCheckboxes');
    if (!container) return;

    container.innerHTML = store.participants.map(p => `
        <label class="participant-checkbox" data-id="${p.id}">
            <input type="checkbox" value="${p.id}">
            <span class="checkmark"></span>
            <span>${p.name}</span>
        </label>
    `).join('');
}

export function renderParticipantsList() {
    const container = document.getElementById('participantsList');
    if (!container) return;

    container.innerHTML = store.participants.map(p => `
        <div class="participant-item">
            <span>${p.name}</span>
            <button class="btn btn-small btn-danger" data-action="deleteParticipant" data-id="${p.id}">✕</button>
        </div>
    `).join('');
}

export function renderParticipantSelects() {
    const invoiceSelect = document.getElementById('invoiceParticipant'); // For old generator if still used?
    const createInvoiceSelect = document.getElementById('createInvoiceParticipant'); // New Modal
    const createReceiptSelect = document.getElementById('createReceiptParticipant'); // New Modal

    const options = '<option value="">Select participant...</option>' +
        store.participants.map(p => `<option value="${p.name}">${p.name}</option>`).join('');

    if (invoiceSelect) invoiceSelect.innerHTML = options;
    if (createInvoiceSelect) createInvoiceSelect.innerHTML = options;
    if (createReceiptSelect) createReceiptSelect.innerHTML = options;
}

// === Expenses ===

export function renderExpensesTable() {
    const tbody = document.getElementById('expensesBody');
    if (!tbody) return;

    if (store.expenses.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="4">
                    <div class="empty-state">
                        <div class="empty-state-icon">📝</div>
                        <p>No expenses yet. Add your first expense above!</p>
                    </div>
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = store.expenses.map(e => {
        // Status badge with better styling
        let statusBadge = e.is_paid
            ? `<span style="display: inline-flex; align-items: center; gap: 4px; padding: 6px 12px; background: rgba(74, 222, 128, 0.2); color: #4ade80; border-radius: 20px; font-size: 0.85rem; font-weight: 500;">
                 ✓ Paid ฿${e.actual_thb.toLocaleString()}
               </span>`
            : `<span style="display: inline-flex; align-items: center; gap: 4px; padding: 6px 12px; background: rgba(251, 191, 36, 0.2); color: #fbbf24; border-radius: 20px; font-size: 0.85rem; font-weight: 500;">
                 ⏳ Pending
               </span>`;

        // Action buttons with consistent sizing
        const btnStyle = 'display: inline-flex; align-items: center; justify-content: center; width: 32px; height: 32px; padding: 0; border-radius: 6px; font-size: 0.9rem;';

        let viewBtn = `<button class="btn btn-small btn-secondary" data-action="viewExpense" data-id="${e.id}" title="View Details" style="${btnStyle}">👁️</button>`;

        let logBtn = !e.is_paid
            ? `<button class="btn btn-small btn-primary admin-only" data-action="logPaymentModal" data-id="${e.id}" title="Log Payment" style="${btnStyle}">✓</button>`
            : '';

        let deleteBtn = '';
        if (e.is_invoiced || (e.invoices && e.invoices.length > 0)) {
            deleteBtn = `<button class="btn btn-small btn-danger admin-only" disabled title="Cannot delete: Invoiced" style="${btnStyle} opacity: 0.4; cursor: not-allowed;">✕</button>`;
        } else {
            deleteBtn = `<button class="btn btn-small btn-danger admin-only" data-action="deleteExpense" data-id="${e.id}" title="Delete" style="${btnStyle}">✕</button>`;
        }

        return `
            <tr>
                <td style="padding: 12px 16px;">
                    <div style="font-weight: 600; color: #ffffff;">${e.name}</div>
                    <div style="font-size: 0.8rem; color: #a0a0b0; margin-top: 4px;">${e.participants.join(', ')}</div>
                </td>
                <td style="padding: 12px 16px; font-weight: 600; color: #4ecdc4;">฿${e.collected_thb.toLocaleString()}</td>
                <td style="padding: 12px 16px;">${statusBadge}</td>
                <td style="padding: 12px 16px;">
                    <div style="display: flex; gap: 6px; justify-content: flex-end;">
                        ${viewBtn}${logBtn}${deleteBtn}
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

export function renderExpenseDetailModal(e) {
    const body = document.getElementById('detailsModalBody');
    const title = document.getElementById('detailsModalTitle');
    const modal = document.getElementById('detailsModal');
    if (!body || !title || !modal) return;

    title.textContent = `📋 ${e.name}`;

    // Variance calculation
    let varianceHtml = '';
    if (e.is_paid) {
        const diff = e.collected_thb - e.actual_thb;
        const diffText = diff >= 0 ? `Saved ฿${diff.toLocaleString()}` : `Over Budget ฿${Math.abs(diff).toLocaleString()}`;
        const bgColor = diff >= 0 ? 'linear-gradient(135deg, #d4edda, #c3e6cb)' : 'linear-gradient(135deg, #f8d7da, #f5c6cb)';
        const textColor = diff >= 0 ? '#155724' : '#721c24';
        const icon = diff >= 0 ? '✅' : '⚠️';

        varianceHtml = `
            <div style="margin-top: 24px; padding: 20px; text-align: center; border-radius: 12px; font-weight: 600; background: ${bgColor}; color: ${textColor}; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <span style="font-size: 1.5rem;">${icon}</span>
                <div style="font-size: 1.2rem; margin-top: 8px;">Variance: ${diffText}</div>
            </div>
        `;
    }

    body.innerHTML = `
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px;">
            <div style="padding: 20px; background: linear-gradient(135deg, #f8f9fa, #e9ecef); border-radius: 12px; border-left: 4px solid #495057;">
                <h3 style="margin: 0 0 16px 0; color: #1f2937; font-size: 1.1rem; display: flex; align-items: center; gap: 8px;">
                    💰 Budget (Collected)
                </h3>
                <div style="display: grid; gap: 12px; font-size: 0.95rem; color: #1f2937;">
                    <div><span style="color: #4b5563;">Original:</span> <strong style="color: #111827;">${formatCurrency(e.amount, e.currency)}</strong></div>
                    <div><span style="color: #4b5563;">Rate:</span> <strong style="color: #111827;">${e.currency === 'JPY' ? e.buffer_rate : '1.0'}</strong></div>
                    <div><span style="color: #4b5563;">Collected:</span> <strong style="color: #047857;">฿${e.collected_thb.toLocaleString()}</strong></div>
                    <div><span style="color: #4b5563;">Per Person:</span> <strong style="color: #111827;">฿${e.per_person_thb.toLocaleString()}</strong></div>
                </div>
                <div style="margin-top: 16px; padding-top: 12px; border-top: 1px solid #d1d5db;">
                    <div style="color: #374151; font-size: 0.85rem; margin-bottom: 8px; font-weight: 500;">Participants:</div>
                    <div style="display: flex; flex-wrap: wrap; gap: 6px;">
                        ${e.participants.map(p => `<span class="participant-tag">${p}</span>`).join('')}
                    </div>
                </div>
                ${e.is_invoiced ? '<div style="margin-top: 12px; padding: 8px 12px; background: #e2e3e5; color: #383d41; border-radius: 6px; text-align: center; font-size: 0.85rem;">📄 Invoiced</div>' : ''}
            </div>
            
            <div style="padding: 20px; background: linear-gradient(135deg, #dbeafe, #bfdbfe); border-radius: 12px; border-left: 4px solid #2563eb;">
                <h3 style="margin: 0 0 16px 0; color: #1e40af; font-size: 1.1rem; display: flex; align-items: center; gap: 8px;">
                    🧾 Actual (Paid)
                </h3>
                ${e.is_paid ? `
                    <div style="display: grid; gap: 12px; font-size: 0.95rem; color: #1f2937;">
                        <div><span style="color: #4b5563;">Paid:</span> <strong style="color: #111827;">${formatCurrency(e.actual_amount, e.actual_currency)}</strong></div>
                        <div><span style="color: #4b5563;">Rate:</span> <strong style="color: #111827;">${e.actual_currency === 'JPY' && e.actual_amount > 0 ? (e.actual_thb / e.actual_amount).toFixed(4) : '1.0'}</strong></div>
                        <div><span style="color: #4b5563;">Final THB:</span> <strong style="color: #1e40af;">฿${e.actual_thb.toLocaleString()}</strong></div>
                        <div><span style="color: #4b5563;">Date:</span> <strong style="color: #111827;">${e.actual_date}</strong></div>
                        <div><span style="color: #4b5563;">Method:</span> <strong style="color: #111827;">${e.actual_method || '-'}</strong></div>
                    </div>
                ` : `
                    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 120px; color: #374151;">
                        <div style="font-size: 2rem; margin-bottom: 12px;">⏳</div>
                        <p style="margin: 0 0 16px 0; font-weight: 500;">Not paid yet</p>
                        <button class="btn btn-primary" data-action="logPaymentModal" data-id="${e.id}">
                            ✓ Log Payment
                        </button>
                    </div>
                `}
            </div>
        </div>
        ${varianceHtml}
    `;

    // Show modal using class
    modal.classList.add('show');
}


// === Invoices Tab ===

export function renderInvoicesTab(data) {
    const tbody = document.getElementById('invoiceHistoryBody');
    if (!tbody) return;

    if (!data.invoices || data.invoices.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6"><div class="empty-state">No invoices generated yet.</div></td></tr>`;
        return;
    }

    tbody.innerHTML = data.invoices.map(inv => {
        const isPaid = inv.status === 'paid';
        const statusClass = isPaid ? 'status-collected' : 'status-pending';
        const statusIcon = isPaid ? '✅' : '⏳';

        let statusDisplay = `<span class="status-badge ${statusClass}">${statusIcon} ${inv.status.toUpperCase()}</span>`;
        if (isPaid && inv.receipt_number) {
            statusDisplay += ` <span class="badge-info" style="font-size: 0.8em;">Rect #${inv.receipt_number}</span>`;
        }

        let deleteBtn = !isPaid
            ? `<button class="btn btn-small btn-danger admin-only" data-action="deleteInvoice" data-id="${inv.id}" title="Delete">✕</button>`
            : '';

        const btnStyle = 'display: inline-flex; align-items: center; justify-content: center; width: 32px; height: 32px; padding: 0; border-radius: 6px; font-size: 0.9rem;';

        return `
            <tr>
                <td style="color: #ffffff; font-weight: 500;">${inv.participant_name}</td>
                <td style="color: #a0a0b0;">#${inv.version}</td>
                <td style="color: #4ecdc4; font-weight: 600;">฿${inv.total_thb.toLocaleString()}</td>
                <td style="color: #a0a0b0;">${formatDate(inv.generated_at)}</td>
                <td>${statusDisplay}</td>
                <td>
                    <div style="display: flex; gap: 6px;">
                        <button class="btn btn-small btn-secondary" data-action="viewInvoice" data-id="${inv.id}" title="View Details" style="${btnStyle}">👁️</button>
                        <button class="btn btn-small btn-primary" onclick="window.open('${API_BASE}/invoices/download/${inv.id}', '_blank')" title="Download PDF" style="${btnStyle}">📥</button>
                        ${deleteBtn}
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

// === Receipts Tab ===

export function renderReceiptsTab(data) {
    const tbody = document.getElementById('receiptHistoryBody');
    if (!tbody) return;

    if (!data.receipts || data.receipts.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7"><div class="empty-state">No receipts generated yet.</div></td></tr>`;
        return;
    }

    tbody.innerHTML = data.receipts.map(r => {
        const invoiceLinks = r.invoice_versions && r.invoice_versions.length > 0
            ? r.invoice_versions.map(v => `#${v}`).join(', ') : '-';

        const btnStyle = 'display: inline-flex; align-items: center; justify-content: center; width: 32px; height: 32px; padding: 0; border-radius: 6px; font-size: 0.9rem;';

        return `
            <tr>
                <td style="color: #ffffff; font-weight: 500;">${r.participant_name}</td>
                <td style="color: #a0a0b0;">#${r.receipt_number}</td>
                <td style="color: #a0a0b0;">${invoiceLinks}</td>
                <td style="color: #4ecdc4; font-weight: 600;">฿${(r.total_thb || 0).toLocaleString()}</td>
                <td style="color: #a0a0b0;">${r.payment_method || '-'}</td>
                <td style="color: #a0a0b0;">${formatDate(r.created_at)}</td>
                <td>
                    <div style="display: flex; gap: 6px;">
                        <button class="btn btn-small btn-secondary" data-action="viewReceipt" data-id="${r.id}" title="View Details" style="${btnStyle}">👁️</button>
                        <button class="btn btn-small btn-success" onclick="window.open('${API_BASE}/receipts/download/${r.id}', '_blank')" title="Download PDF" style="${btnStyle}">📥</button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

// === Payments Tab ===

export function renderPaymentsTab(expenses) {
    const tbody = document.getElementById('paymentsBody');
    const totalEl = document.getElementById('paymentsTotal').querySelector('.total-amount');
    if (!tbody) return;

    // Filter paid expenses and sort by actual date desc
    const payments = expenses.filter(e => e.is_paid).sort((a, b) => {
        return new Date(b.actual_date) - new Date(a.actual_date);
    });

    if (payments.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7"><div class="empty-state">No payments recorded yet.</div></td></tr>`;
        totalEl.textContent = '฿0';
        return;
    }

    let totalPaid = 0;

    tbody.innerHTML = payments.map(p => {
        totalPaid += p.actual_thb;
        const rate = p.actual_currency === 'JPY' && p.actual_amount > 0 ? (p.actual_thb / p.actual_amount).toFixed(4) : '-';

        const btnStyle = 'display: inline-flex; align-items: center; justify-content: center; width: 32px; height: 32px; padding: 0; border-radius: 6px; font-size: 0.9rem;';

        return `
            <tr>
                <td style="color: #ffffff;">${formatDate(p.actual_date)}</td>
                <td>
                    <div style="font-weight: 500; color: #ffffff;">${p.name}</div>
                    <div style="font-size: 0.8rem; color: #a0a0b0;">${p.participants.length} participants</div>
                </td>
                <td style="color: #a0a0b0;">${p.actual_method || '-'}</td>
                <td style="color: #ffffff;">${formatCurrency(p.actual_amount, p.actual_currency)}</td>
                <td style="color: #a0a0b0;">${rate}</td>
                <td style="color: #4ade80; font-weight: 600;">฿${p.actual_thb.toLocaleString()}</td>
                <td>
                    <button class="btn btn-small btn-secondary" data-action="viewExpense" data-id="${p.id}" title="View Details" style="${btnStyle}">👁️</button>
                </td>
            </tr>
        `;
    }).join('');

    totalEl.textContent = `฿${totalPaid.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

// === Overview (Dashboard) ===

export function renderOverview(data) {
    const kpiContainer = document.getElementById('financialKPIs');
    const opStmtContainer = document.getElementById('operatingStatementTbl');

    // Default data structure if missing (safety)
    const financial = data.financial_dashboard || {
        net_cash_position: 0,
        collection_ratio: 0,
        accounts_receivable: 0,
        total_inflow: 0,
        total_outflow: 0,
        total_committed_spend: 0
    };

    // 1. Render KPIs
    if (kpiContainer) {
        const netPosColor = financial.net_cash_position >= 0 ? '#4ade80' : '#f87171';
        const netPosIcon = financial.net_cash_position >= 0 ? '📈' : '📉';

        kpiContainer.innerHTML = `
            <!-- Net Position -->
            <div style="background: rgba(15, 15, 26, 0.6); padding: 20px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1);">
                <div style="color: #a0a0b0; font-size: 0.85rem; margin-bottom: 8px;">Net Cash Position</div>
                <div style="font-size: 1.5rem; font-weight: 700; color: ${netPosColor};">
                    ${netPosIcon} ฿${financial.net_cash_position.toLocaleString()}
                </div>
                <div style="color: #6b7280; font-size: 0.75rem; margin-top: 4px;">Liquidity Available</div>
            </div>

            <!-- Collection Ratio -->
            <div style="background: rgba(15, 15, 26, 0.6); padding: 20px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1);">
                <div style="color: #a0a0b0; font-size: 0.85rem; margin-bottom: 8px;">Collection Ratio</div>
                <div style="font-size: 1.5rem; font-weight: 700; color: #60a5fa;">
                    ${financial.collection_ratio}%
                </div>
                <div style="color: #6b7280; font-size: 0.75rem; margin-top: 4px;">% of Invoiced Collected</div>
            </div>

            <!-- Accounts Receivable -->
            <div style="background: rgba(15, 15, 26, 0.6); padding: 20px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1);">
                <div style="color: #a0a0b0; font-size: 0.85rem; margin-bottom: 8px;">Accounts Receivable</div>
                <div style="font-size: 1.5rem; font-weight: 700; color: #fbbf24;">
                    ฿${financial.accounts_receivable.toLocaleString()}
                </div>
                <div style="color: #6b7280; font-size: 0.75rem; margin-top: 4px;">Pending Collections</div>
            </div>

            <!-- Total Committed Spend -->
            <div style="background: rgba(15, 15, 26, 0.6); padding: 20px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1);">
                <div style="color: #a0a0b0; font-size: 0.85rem; margin-bottom: 8px;">Total Committed Spend</div>
                <div style="font-size: 1.5rem; font-weight: 700; color: #e2e8f0;">
                    ฿${financial.total_committed_spend.toLocaleString()}
                </div>
                <div style="color: #6b7280; font-size: 0.75rem; margin-top: 4px;">Total Invoiced Expenses</div>
            </div>
        `;
    }

    // 2. Render Operating Statement
    if (opStmtContainer) {
        opStmtContainer.innerHTML = `
            <table style="width: 100%; border-collapse: collapse; font-family: monospace, sans-serif;">
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.1);">
                    <td style="padding: 12px 0; color: #a0a0b0;">Total Invoiced Income</td>
                    <td style="padding: 12px 0; text-align: right; color: #e2e8f0;">฿${financial.total_committed_spend.toLocaleString()}</td>
                </tr>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.1);">
                    <td style="padding: 12px 0; color: #f87171;">Less: Unpaid Invoices (AR)</td>
                    <td style="padding: 12px 0; text-align: right; color: #f87171;">(฿${financial.accounts_receivable.toLocaleString()})</td>
                </tr>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.1); background: rgba(255,255,255,0.02);">
                    <td style="padding: 12px 0; font-weight: 600; color: #fff;">= Net Cash Collected (Inflow)</td>
                    <td style="padding: 12px 0; text-align: right; font-weight: 600; color: #4ade80;">฿${financial.total_inflow.toLocaleString()}</td>
                </tr>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.1);">
                    <td style="padding: 12px 0; color: #f87171;">Less: Paid Expenses (Outflow)</td>
                    <td style="padding: 12px 0; text-align: right; color: #f87171;">(฿${financial.total_outflow.toLocaleString()})</td>
                </tr>
                <tr>
                    <td style="padding: 16px 0; font-size: 1.1rem; font-weight: 700; color: #fff;">Net Cash Position</td>
                    <td style="padding: 16px 0; text-align: right; font-size: 1.1rem; font-weight: 700; color: ${financial.net_cash_position >= 0 ? '#4ade80' : '#f87171'};">
                        ฿${financial.net_cash_position.toLocaleString()}
                    </td>
                </tr>
            </table>
        `;
    }

    // 3. Render Spend Performance (Progress Bar)
    const perfContainer = document.getElementById('spendPerformanceCard');
    if (perfContainer) {
        // Fallback zeroes
        // Extract values
        const budget = financial.total_budget || 0;
        const actual = financial.actual_paid || 0;
        const pending = financial.pending_budget || 0;
        const savings = financial.savings || 0;

        const savingsColor = savings >= 0 ? '#4ade80' : '#f87171';
        const savingsLabel = savings >= 0 ? 'Realized Savings' : 'Realized Overrun';

        perfContainer.innerHTML = `
            <h3 style="margin-bottom: 24px; font-size: 1.1rem; color: #e2e8f0; display: flex; align-items: center; justify-content: space-between;">
                <span>🎯 Spend Performance <span style="font-size: 0.8rem; color: #a0a0b0; font-weight: 400;">(Planned vs Actual)</span></span>
                <span style="font-size: 0.9rem; color: ${savingsColor}; font-weight: 600;">
                    ${savingsLabel}: ฿${Math.abs(savings).toLocaleString()}
                </span>
            </h3>
            
            <div style="position: relative; height: 120px; width: 100%; margin-bottom: 20px;">
                <canvas id="spendPerformanceChart"></canvas>
            </div>
            
            <!-- Stats -->
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px;">
                <div style="text-align: center;">
                    <div style="font-size: 0.8rem; color: #a0a0b0; margin-bottom: 4px;">Total Planned</div>
                    <div style="font-size: 1rem; font-weight: 600; color: #fff;">฿${budget.toLocaleString()}</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 0.8rem; color: #60a5fa; margin-bottom: 4px;">Actual Paid</div>
                    <div style="font-size: 1rem; font-weight: 600; color: #60a5fa;">฿${actual.toLocaleString()}</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 0.8rem; color: #fbbf24; margin-bottom: 4px;">Pending Payment</div>
                    <div style="font-size: 1rem; font-weight: 600; color: #fbbf24;">฿${pending.toLocaleString()}</div>
                </div>
            </div>
        `;

        // Render Chart
        setTimeout(() => {
            const ctx = document.getElementById('spendPerformanceChart');
            if (ctx) {
                if (window.mySpendChart) window.mySpendChart.destroy();

                // If savings < 0 (Overrun), we don't show a negative bar, we just show Actual + Pending which will exceed Budget.
                // If savings > 0, we show a green "Savings" segment to fill the bar up to Budget.
                const visualSavings = savings > 0 ? savings : 0;

                window.mySpendChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: ['Budget'],
                        datasets: [
                            {
                                label: 'Actual Paid',
                                data: [actual],
                                backgroundColor: '#60a5fa',
                                barThickness: 40
                            },
                            {
                                label: 'Pending Payment',
                                data: [pending],
                                backgroundColor: '#fbbf24',
                                barThickness: 40
                            },
                            {
                                label: 'Realized Savings',
                                data: [visualSavings],
                                backgroundColor: 'rgba(74, 222, 128, 0.3)', // Transparent green
                                borderColor: '#4ade80',
                                borderWidth: 1,
                                barThickness: 40,
                                borderSkipped: false
                            }
                        ]
                    },
                    options: {
                        indexAxis: 'y',
                        responsive: true,
                        maintainAspectRatio: false,
                        layout: { padding: { top: 40 } }, // More space for label
                        scales: {
                            x: {
                                stacked: true,
                                grid: { color: 'rgba(255,255,255,0.05)' },
                                ticks: { color: '#6b7280', callback: (val) => '฿' + val.toLocaleString() },
                                max: Math.max(budget, actual + pending) * 1.15 // More space for label
                            },
                            y: {
                                stacked: true,
                                display: false
                            }
                        },
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                callbacks: {
                                    label: function (context) {
                                        let label = context.dataset.label || '';
                                        if (label) { label += ': '; }
                                        if (context.parsed.x !== null) { label += '฿' + context.parsed.x.toLocaleString(); }
                                        return label;
                                    }
                                }
                            }
                        }
                    },
                    plugins: [{
                        id: 'budgetLine',
                        afterDraw: (chart) => {
                            const ctx = chart.ctx;
                            const xAxis = chart.scales.x;
                            const yAxis = chart.scales.y;
                            const x = xAxis.getPixelForValue(budget);
                            const top = yAxis.top;
                            const bottom = yAxis.bottom;

                            if (x < xAxis.left || x > xAxis.right) return; // Don't draw if out of bounds (unlikely given max)

                            ctx.save();
                            // Draw Line
                            ctx.beginPath();
                            ctx.moveTo(x, top - 10);
                            ctx.lineTo(x, bottom);
                            ctx.lineWidth = 2;
                            ctx.strokeStyle = '#e2e8f0'; // Light white/gray
                            ctx.setLineDash([5, 5]);
                            ctx.stroke();

                            // Draw Label
                            ctx.fillStyle = '#e2e8f0';
                            ctx.font = 'bold 0.75rem Inter, sans-serif';
                            ctx.textAlign = 'center';
                            ctx.fillText('Total Planned', x, top - 15);
                            ctx.restore();
                        }
                    }]
                });
            }
        }, 0);
    }

    // 3. Render Cash Flow Chart
    if (data.cash_flow) {
        const ctx = document.getElementById('cashFlowChart');
        if (ctx) {
            if (window.myCashFlowChart) window.myCashFlowChart.destroy();

            window.myCashFlowChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.cash_flow.labels,
                    datasets: [
                        {
                            type: 'line',
                            label: 'Cumulative Balance',
                            data: data.cash_flow.cumulative,
                            borderColor: '#60a5fa',
                            backgroundColor: 'rgba(96, 165, 250, 0.1)',
                            borderWidth: 2,
                            tension: 0.3,
                            pointRadius: 0,
                            pointHoverRadius: 4,
                            yAxisID: 'y',
                            order: 0
                        },
                        {
                            label: 'Inflow',
                            data: data.cash_flow.inflow,
                            backgroundColor: '#4ade80',
                            order: 1
                        },
                        {
                            label: 'Outflow',
                            data: data.cash_flow.outflow,
                            backgroundColor: '#f87171',
                            order: 2
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: { mode: 'index', intersect: false },
                    plugins: {
                        legend: { labels: { color: '#a0a0b0' } }
                    },
                    scales: {
                        y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#6b7280' } },
                        x: { grid: { display: false }, ticks: { color: '#6b7280' } }
                    }
                }
            });
        }
    }

    // 4. Render Expense Breakdown Chart
    if (data.expense_breakdown) {
        const ctx = document.getElementById('expenseChart');
        if (ctx) {
            if (window.myExpenseChart) window.myExpenseChart.destroy();

            window.myExpenseChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: data.expense_breakdown.labels,
                    datasets: [{
                        data: data.expense_breakdown.data,
                        backgroundColor: data.expense_breakdown.colors,
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '65%',
                    plugins: {
                        legend: {
                            position: 'right',
                            labels: { color: '#a0a0b0', boxWidth: 12 }
                        }
                    }
                }
            });
        }
    }
}

// === Create Invoice Modal ===

export function renderCreateInvoiceModal(participantName, unbilledExpenses) {
    const select = document.getElementById('createInvoiceParticipant');
    if (select) {
        select.value = participantName || "";
    }

    const section = document.getElementById('createInvoiceExpensesSection');
    const emptyMsg = document.getElementById('createInvoiceEmpty');
    const list = document.getElementById('createInvoiceExpensesList');
    const btn = document.getElementById('doGenerateInvoiceBtn');
    const totalEl = document.getElementById('createInvoiceTotal');

    if (!participantName) {
        if (section) section.style.display = 'none';
        if (emptyMsg) emptyMsg.style.display = 'none';
        if (btn) btn.disabled = true;
        return;
    }

    if (!unbilledExpenses || unbilledExpenses.length === 0) {
        if (section) section.style.display = 'none';
        if (emptyMsg) emptyMsg.style.display = 'block';
        if (btn) btn.disabled = true;
    } else {
        if (emptyMsg) emptyMsg.style.display = 'none';
        if (section) section.style.display = 'block';

        // Render checkboxes
        list.innerHTML = unbilledExpenses.map(exp => `
            <label class="invoice-checkbox-row" style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.1);">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <input type="checkbox" class="create-invoice-check" value="${exp.expense_id}" data-amount="${exp.your_share_thb}" checked>
                    <div>
                        <div style="color: #ffffff; font-weight: 500;">${exp.name}</div>
                        <div style="color: #a0a0b0; font-size: 0.85rem;">${formatCurrency(exp.original_amount, exp.currency)}</div>
                    </div>
                </div>
                <div style="color: #4ecdc4; font-weight: 600;">฿${exp.your_share_thb.toLocaleString()}</div>
            </label>
            `).join('');

        // Initial calculation
        const calculateTotal = () => {
            let total = 0;
            const checks = list.querySelectorAll('.create-invoice-check:checked');
            checks.forEach(c => total += parseFloat(c.dataset.amount || 0));
            totalEl.textContent = `฿${total.toLocaleString()} `;
            btn.disabled = total > 0 ? false : true;
        };
        calculateTotal();

        // Bind events
        const checks = list.querySelectorAll('.create-invoice-check');
        const selectAll = document.getElementById('createInvoiceSelectAll');

        checks.forEach(c => c.addEventListener('change', () => {
            calculateTotal();
            if (selectAll) selectAll.checked = Array.from(checks).every(ch => ch.checked);
        }));

        if (selectAll) {
            selectAll.checked = true;
            selectAll.onclick = () => {
                checks.forEach(c => c.checked = selectAll.checked);
                calculateTotal();
            };
        }
    }
}

// === Create Receipt Modal ===

export function renderCreateReceiptModal(participantName, unpaidInvoices) {
    const createReceiptParticipant = document.getElementById('createReceiptParticipant');
    if (createReceiptParticipant) {
        // Assuming participant selection happened via UI logic, just ensure select reflects it if passed
        // If participantName is passed empty, we are resetting.
        if (participantName) {
            createReceiptParticipant.value = participantName;
        }
    }

    const section = document.getElementById('createReceiptInvoicesSection');
    const emptyMsg = document.getElementById('createReceiptEmpty');
    const list = document.getElementById('createReceiptInvoicesList');
    const btn = document.getElementById('doGenerateReceiptBtn');
    const totalEl = document.getElementById('createReceiptTotal');

    if (!participantName) {
        if (section) section.style.display = 'none';
        if (emptyMsg) emptyMsg.style.display = 'none';
        if (btn) btn.disabled = true;
        return;
    }

    if (!unpaidInvoices || unpaidInvoices.length === 0) {
        if (section) section.style.display = 'none';
        if (emptyMsg) emptyMsg.style.display = 'block';
        if (btn) btn.disabled = true;
    } else {
        if (emptyMsg) emptyMsg.style.display = 'none';
        if (section) section.style.display = 'block';

        list.innerHTML = unpaidInvoices.map(inv => `
            <label class="invoice-checkbox-row" style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.1);">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <input type="checkbox" class="create-receipt-check" value="${inv.id}" data-amount="${inv.total_thb}" checked>
                    <div>
                        <div style="color: #ffffff; font-weight: 500;">Invoice #${inv.version}</div>
                        <div style="color: #a0a0b0; font-size: 0.85rem;">${formatDate(inv.generated_at)}</div>
                    </div>
                </div>
                <div style="color: #4ecdc4; font-weight: 600;">฿${inv.total_thb.toLocaleString()}</div>
            </label>
            `).join('');

        const calculateTotal = () => {
            let total = 0;
            const checks = list.querySelectorAll('.create-receipt-check:checked');
            checks.forEach(c => total += parseFloat(c.dataset.amount || 0));
            totalEl.textContent = `฿${total.toLocaleString()} `;
            btn.disabled = total > 0 ? false : true;
        };
        calculateTotal();

        // Bind events
        const checks = list.querySelectorAll('.create-receipt-check');
        checks.forEach(c => c.addEventListener('change', calculateTotal));
    }
}

export function renderInvoiceDetailsModal(data) {
    const titleEl = document.getElementById('detailsModalTitle');
    const container = document.getElementById('detailsModalBody');
    if (titleEl) titleEl.textContent = `Invoice #${data.version} `;
    if (!container) return;

    let itemsInfo = '<p class="text-muted" style="text-align:center; padding:20px;">No new expenses.</p>';

    if (data.new_expenses && data.new_expenses.length > 0) {
        itemsInfo = `
            <div class="invoice-section">
                <div class="invoice-section-title">Expense Breakdown</div>
                <table class="premium-table">
                    <thead>
                        <tr>
                            <th>Item</th>
                            <th>Cost</th>
                            <th>Share</th>
                            <th class="text-right">Your Share</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.new_expenses.map(item => `
                            <tr>
                                <td>${item.name}</td>
                                <td>${formatCurrency(item.original_amount, item.currency)}
                                    ${item.currency === 'JPY' ? `<br><span style="font-size:0.7em; color:#9ca3af">@ ${item.buffer_rate}</span>` : ''}
                                </td>
                                <td>${item.share}</td>
                                <td class="text-right" style="font-weight:600;">฿${item.your_share_thb.toLocaleString()}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
            `;
    }

    container.innerHTML = `
            <div class="invoice-paper" style="box-shadow: none; border: 1px solid #e5e7eb;">
            <div class="invoice-header">
                <div class="invoice-brand">
                    <p style="color: #6b7280; font-size: 0.85rem; margin-bottom: 4px;">Nine Travel Co., Ltd.</p>
                    <h3>INVOICE</h3>
                    <p style="color: #6b7280; font-size: 0.9rem;">${store.settings.trip_name}</p>
                </div>
                <div class="invoice-meta">
                     <p>Invoice #${data.version}</p>
                     <p>${formatDate(data.generated_at)}</p>
                </div>
            </div>
            
            <div style="margin-bottom: 24px;">
                <strong>Bill To:</strong> ${data.participant_name}
            </div>

            ${itemsInfo}

            <div class="total-box">
                <span class="total-label">Total Due</span>
                <span class="total-amount">฿${data.grand_total.toLocaleString()}</span>
            </div>
            
            <div style="margin-top: 24px; text-align: right;">
                <button class="btn btn-primary" onclick="window.open('${API_BASE}/invoices/download/${data.id}', '_blank');">
                    📥 Download PDF
                </button>
            </div>
        </div >
            `;
}

export function renderReceiptDetailsModal(data) {
    const titleEl = document.getElementById('detailsModalTitle');
    const container = document.getElementById('detailsModalBody');
    if (titleEl) titleEl.textContent = `Receipt #${data.receipt_number} `;
    if (!container) return;

    // Items Table
    let itemsHtml = '';
    if (data.items && data.items.length > 0) {
        const itemRows = data.items.map(item => `
            < tr >
                <td>
                    <div style="font-weight: 500;">${item.expense_name}</div>
                </td>
                <td>${formatCurrency(item.original_amount, item.currency)}</td>
                <td>${item.buffer_rate || '-'}</td>
                <td>${item.share}</td>
                <td class="text-right">฿${item.amount_paid.toLocaleString()}</td>
            </tr >
            `).join('');

        itemsHtml = `
            < div class="invoice-section" >
                <div class="invoice-section-title">Payment For</div>
                <table class="premium-table">
                    <thead>
                        <tr>
                             <th style="width: 35%">Item</th>
                             <th>Original</th>
                             <th>Rate</th>
                             <th>Share</th>
                             <th class="text-right">Paid (THB)</th>
                        </tr>
                    </thead>
                    <tbody>${itemRows}</tbody>
                </table>
            </div >
            `;
    }

    // Main Layout (Invoice Paper Style)
    container.innerHTML = `
            < div class="invoice-paper" style = "box-shadow: none; border: 1px solid #e5e7eb;" >
            <div class="invoice-header">
                <div class="invoice-brand">
                    <p style="color: #6b7280; font-size: 0.85rem; margin-bottom: 4px;">Nine Travel Co., Ltd.</p>
                    <h3>PAYMENT RECEIPT</h3>
                    <p style="color: #6b7280; font-size: 0.9rem;">${store.settings.trip_name}</p>
                </div>
                <div class="invoice-meta">
                    <p><strong>Receipt #${data.receipt_number}</strong></p>
                    <p>Date: ${formatDate(data.generated_at)}</p>
                    <p>Method: ${data.payment_method || 'N/A'}</p>
                </div>
            </div>
            
            <div class="invoice-section">
                <p>
                    <strong>Received From:</strong> <span style="font-size: 1.1rem; color: #111827;">${data.participant_name}</span>
                </p>
            </div>

            ${itemsHtml}

            <div class="total-box success">
                <span class="total-label">Total Received</span>
                <span class="total-amount">฿${data.total_paid.toLocaleString()}</span>
            </div>
            
            <div style="margin-top: 24px; text-align: center;">
                 <a href="/api/receipts/download/${data.id}" target="_blank" class="btn btn-secondary">
                    📥 Download PDF
                </a>
            </div>
        </div >
            `;
}

// === Reconciliation ===

export function renderReconciliationTable(data) {
    // NOTE: This function now renders a GRID of cards to #reconciliationGrid
    const grid = document.getElementById('reconciliationGrid');
    if (!grid) return; // Grid container not found

    console.log('DEBUG RECON DATA:', data);

    // Handle list if data is list (from API)
    const reconciliation = Array.isArray(data) ? data : (data.reconciliation || []);

    if (reconciliation.length === 0) {
        grid.innerHTML = `
            <div class="empty-state" style="grid-column: 1 / -1;">
                <div class="empty-state-icon">🤷‍♂️</div>
                <p>No reconciliation data available yet.</p>
            </div>
        `;
        return;
    }

    grid.innerHTML = reconciliation.map(rec => {
        const surplus = rec.surplus_deficit || 0;
        const isSurplus = surplus >= 0;
        const statusClass = isSurplus ? 'surplus' : 'deficit';
        const statusLabel = isSurplus ? 'Surplus' : 'Deficit';

        // Avatar letter
        const initial = rec.participant_name ? rec.participant_name.charAt(0).toUpperCase() : '?';

        return `
            <div class="recon-card ${statusClass}">
                <div class="recon-header">
                    <div class="recon-avatar">${initial}</div>
                    <div class="recon-info">
                        <h3>${rec.participant_name}</h3>
                        <p>Participant</p>
                    </div>
                </div>

                <div class="recon-stats">
                    <div class="recon-stat-item">
                        <span class="recon-stat-label">Collected</span>
                        <span class="recon-stat-value">฿${(rec.total_collected || 0).toLocaleString()}</span>
                    </div>
                    <div class="recon-stat-item">
                        <span class="recon-stat-label">Actual Cost</span>
                        <span class="recon-stat-value">฿${(rec.total_actual || 0).toLocaleString()}</span>
                    </div>
                </div>

                <div class="recon-net">
                    <div class="recon-net-label">Net Position (${statusLabel})</div>
                    <div class="recon-net-amount">${isSurplus ? '+' : '-'}฿${Math.abs(surplus).toLocaleString()}</div>
                </div>

                <div class="recon-actions">
                    <button class="btn btn-secondary btn-small" style="width: 100%; justify-content: center;"
                        data-action="showRefundDetail" 
                        data-name="${rec.participant_name}">
                        View Breakdown
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

// === Refund Detail (Modal) ===
export function renderRefundDetail(data) {
    // Target the shared Details Modal
    const modal = document.getElementById('detailsModal');
    const title = document.getElementById('detailsModalTitle');
    const body = document.getElementById('detailsModalBody');

    if (!modal || !body) return;

    // Set Title
    if (title) title.textContent = `Refund Details: ${data.participant_name}`;

    // Helper for table rows
    const renderRows = (items, isPaid = false) => {
        if (!items || items.length === 0) return '<tr><td colspan="4" class="text-muted text-center">No items</td></tr>';

        return items.map(item => `
            <tr>
                <td>${item.expense_name}</td>
                <td>${formatCurrency(isPaid ? item.paid_amount : item.original_amount, isPaid ? item.paid_currency : item.currency)}</td>
                <td>${item.share}</td>
                <td class="text-right">฿${(isPaid ? item.your_cost_thb : item.collected_thb || 0).toLocaleString()}</td>
            </tr>
        `).join('');
    };

    const collectedRows = renderRows(data.collected_items);
    const actualRows = renderRows(data.actual_items, true);

    const refundAmount = data.refund_amount || 0;
    const isRefund = refundAmount >= 0; // Positive = Refund Due to person
    const statusColor = isRefund ? 'text-success' : 'text-danger';
    const statusLabel = isRefund ? 'Refund Due' : 'Payment Required';
    const statusIcon = isRefund ? '💰' : '💸';

    // 2-Column Grid Layout
    body.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; padding-bottom: 16px; border-bottom: 1px solid rgba(255,255,255,0.1);">
            <div>
                <h3 style="margin: 0;">${data.participant_name}</h3>
                <p style="color: #a0a0b0; margin: 4px 0 0 0; font-size: 0.9rem;">
                    Trip: ${data.trip_name || 'N/A'} | Date: ${data.generated_at || new Date().toISOString().split('T')[0]}
                </p>
            </div>
            <div style="text-align: right;">
                 <h2 class="${statusColor}" style="margin: 0; font-size: 1.8rem;">
                    ${isRefund ? '+' : '-'}฿${Math.abs(refundAmount).toLocaleString()}
                 </h2>
                 <span style="font-size: 0.85rem; color: #a0a0b0; text-transform: uppercase; letter-spacing: 0.05em;">${statusLabel}</span>
            </div>
        </div>

        <div class="refund-grid">
            <!-- Left Column: Collected -->
            <div class="refund-column">
                <h4 style="color: #4ecdc4;">
                    <span>📥</span> Collected (Budget)
                </h4>
                <div class="table-responsive-wrapper">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Item</th>
                                <th>Orig.</th>
                                <th>Share</th>
                                <th class="text-right">THB</th>
                            </tr>
                        </thead>
                        <tbody>${collectedRows}</tbody>
                    </table>
                </div>
                <div class="refund-summary-box" style="color: #4ecdc4;">
                    Total Collected: ฿${(data.total_collected || 0).toLocaleString()}
                </div>
            </div>

            <!-- Right Column: Actual -->
            <div class="refund-column">
                <h4 style="color: #f59e0b;">
                    <span>📤</span> Actual Cost
                </h4>
                <div class="table-responsive-wrapper">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Item</th>
                                <th>Paid</th>
                                <th>Share</th>
                                <th class="text-right">THB</th>
                            </tr>
                        </thead>
                        <tbody>${actualRows}</tbody>
                    </table>
                </div>
                <div class="refund-summary-box" style="color: #f59e0b;">
                    Total Cost: ฿${(data.total_actual || 0).toLocaleString()}
                </div>
            </div>
        </div>

        <div style="margin-top: 32px; display: flex; justify-content: flex-end;">
             <button class="btn btn-primary" onclick="window.open('/api/refunds/${data.participant_name}/pdf/download', '_blank')">
                📄 Download Official PDF Report
            </button>
        </div>
    `;

    // Show Modal
    modal.classList.add('show');
}
