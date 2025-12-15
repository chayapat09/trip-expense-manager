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

// === Overview (Dashboard) ===

export function renderOverview(data) {
    const statsContainer = document.getElementById('overviewStats');
    if (statsContainer) {
        // Calculate totals dynamically if not provided or just use data.stats
        const stats = data.stats || {
            total_invoices: 0, total_invoiced_amount: 0,
            paid_invoices: 0, paid_amount: 0,
            unpaid_invoices: 0, unpaid_amount: 0,
            total_receipts: 0, total_received: 0
        };

        statsContainer.innerHTML = `
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-icon">📄</div>
                    <div class="stat-value">${stats.total_invoices}</div>
                    <div class="stat-label">Total Invoices</div>
                    <div class="stat-amount">฿${stats.total_invoiced_amount.toLocaleString()}</div>
                </div>
                <div class="stat-card stat-success">
                    <div class="stat-icon">✅</div>
                    <div class="stat-value">${stats.paid_invoices}</div>
                    <div class="stat-label">Paid Invoices</div>
                    <div class="stat-amount">฿${stats.paid_amount.toLocaleString()}</div>
                </div>
                <div class="stat-card stat-warning">
                    <div class="stat-icon">⏳</div>
                    <div class="stat-value">${stats.unpaid_invoices}</div>
                    <div class="stat-label">Pending Payment</div>
                    <div class="stat-amount">฿${stats.unpaid_amount.toLocaleString()}</div>
                </div>
                <div class="stat-card stat-primary">
                    <div class="stat-icon">🧾</div>
                    <div class="stat-value">${stats.total_receipts}</div>
                    <div class="stat-label">Receipts Generated</div>
                    <div class="stat-amount">฿${stats.total_received.toLocaleString()}</div>
                </div>
            </div>
        `;
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
            totalEl.textContent = `฿${total.toLocaleString()}`;
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
            totalEl.textContent = `฿${total.toLocaleString()}`;
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
    if (titleEl) titleEl.textContent = `Invoice #${data.version}`;
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
        </div>
    `;
}

export function renderReceiptDetailsModal(data) {
    const titleEl = document.getElementById('detailsModalTitle');
    const container = document.getElementById('detailsModalBody');
    if (titleEl) titleEl.textContent = `Receipt #${data.receipt_number}`;
    if (!container) return;

    // Items Table
    let itemsHtml = '';
    if (data.items && data.items.length > 0) {
        const itemRows = data.items.map(item => `
            <tr>
                <td>
                    <div style="font-weight: 500;">${item.expense_name}</div>
                </td>
                <td>${formatCurrency(item.original_amount, item.currency)}</td>
                <td>${item.buffer_rate || '-'}</td>
                <td>${item.share}</td>
                <td class="text-right">฿${item.amount_paid.toLocaleString()}</td>
            </tr>
        `).join('');

        itemsHtml = `
            <div class="invoice-section">
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
            </div>
         `;
    }

    // Main Layout (Invoice Paper Style)
    container.innerHTML = `
        <div class="invoice-paper" style="box-shadow: none; border: 1px solid #e5e7eb;">
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
        </div>
    `;
}

// === Reconciliation ===

export function renderReconciliationTable(data) {
    const tbody = document.getElementById('reconciliationBody');
    if (!tbody) return;

    // Handle list if data is list (from API)
    const reconciliation = Array.isArray(data) ? data : (data.reconciliation || []);

    if (reconciliation.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5"><div class="empty-state">No reconciliation data available.</div></td></tr>`;
        return;
    }

    tbody.innerHTML = reconciliation.map(rec => {
        const surplus = rec.surplus_deficit || 0;
        const isSurplus = surplus >= 0;
        let diffColor = isSurplus ? 'text-success' : 'text-danger';
        let diffText = isSurplus ? `+฿${surplus.toLocaleString()}` : `-฿${Math.abs(surplus).toLocaleString()}`;
        if (surplus === 0) { diffColor = 'text-muted'; diffText = '0'; }

        return `
            <tr>
                <td><strong>${rec.participant_name}</strong></td>
                <td>฿${(rec.total_collected || 0).toLocaleString()}</td>
                <td>฿${(rec.total_actual || 0).toLocaleString()}</td>
                <td class="${diffColor}"><strong>${diffText}</strong></td>
                <td>
                    <button class="btn btn-small btn-secondary" data-action="showRefundDetail" data-name="${rec.participant_name}">👁️ Details</button>
                </td>
            </tr>
        `;
    }).join('');
}

export function renderRefundDetail(data) {
    const container = document.getElementById('refundDetail');
    const card = document.getElementById('refundDetailCard');
    if (!container || !card) return;

    card.style.display = 'block';

    // Build collected items table
    const collectedRows = (data.collected_items || []).map(item => `
        <tr>
            <td>${item.expense_name}</td>
            <td>${formatCurrency(item.original_amount, item.currency)}</td>
            <td>${item.share}</td>
            <td>฿${(item.collected_thb || 0).toLocaleString()}</td>
        </tr>
    `).join('');

    // Build actual items table
    const actualRows = (data.actual_items || []).map(item => `
        <tr>
            <td>${item.expense_name}</td>
            <td>${formatCurrency(item.paid_amount, item.paid_currency)}</td>
            <td>${item.share}</td>
            <td>฿${(item.your_cost_thb || 0).toLocaleString()}</td>
        </tr>
    `).join('');

    const refundAmount = data.refund_amount || 0;
    const isRefund = refundAmount >= 0;

    container.innerHTML = `
        <div style="margin-bottom:20px;">
            <h3>Refund Breakdown for ${data.participant_name}</h3>
            <p style="color: #a0a0b0;">Trip: ${data.trip_name} | Generated: ${data.generated_at}</p>
        </div>
        
        <div style="margin-bottom: 24px;">
            <h4 style="color: #4ecdc4; margin-bottom: 12px;">💰 Collected (Budgeted)</h4>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Item</th>
                        <th>Original</th>
                        <th>Share</th>
                        <th>Collected THB</th>
                    </tr>
                </thead>
                <tbody>${collectedRows}</tbody>
            </table>
            <div style="text-align: right; margin-top: 8px; font-weight: 600; color: #4ecdc4;">
                Total Collected: ฿${(data.total_collected || 0).toLocaleString()}
            </div>
        </div>
        
        <div style="margin-bottom: 24px;">
            <h4 style="color: #f59e0b; margin-bottom: 12px;">🧾 Actual (Paid)</h4>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Item</th>
                        <th>Paid</th>
                        <th>Share</th>
                        <th>Your Cost THB</th>
                    </tr>
                </thead>
                <tbody>${actualRows}</tbody>
            </table>
            <div style="text-align: right; margin-top: 8px; font-weight: 600; color: #f59e0b;">
                Total Actual: ฿${(data.total_actual || 0).toLocaleString()}
            </div>
        </div>
        
        <div class="total-box ${isRefund ? 'success' : ''}" style="margin-top:20px;">
            <span class="total-label">${isRefund ? 'Refund Due' : 'Additional Payment Required'}</span>
            <span class="total-amount ${isRefund ? 'text-success' : 'text-danger'}">
                ${isRefund ? '+' : '-'}฿${Math.abs(refundAmount).toLocaleString()}
            </span>
        </div>
        <div style="text-align: right; margin-top: 20px;">
             <button class="btn btn-primary" onclick="window.open('${API_BASE}/refunds/${data.participant_name}/pdf/download', '_blank')">
                📥 Download Refund Report
            </button>
        </div>
    `;
}
