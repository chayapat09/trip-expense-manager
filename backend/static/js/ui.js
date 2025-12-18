import { apiCall, API_BASE } from './api.js';
import * as Renderers from './renderers.js';
import { store } from './store.js';

export function showToast(message, type = 'info') {
    document.querySelectorAll('.toast').forEach(t => t.remove());

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed; bottom: 24px; right: 24px; padding: 16px 24px;
        background: ${type === 'success' ? '#4ade80' : type === 'error' ? '#f87171' : '#6c63ff'};
        color: white; border-radius: 12px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
        z-index: 2000; animation: slideUp 0.3s ease;
    `;
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

export function setupTabs(loadCallback) {
    // Function to activate a tab by ID
    const activateTab = (tabId) => {
        const validTabs = ['expenses', 'invoices', 'receipts', 'payments', 'refunds', 'overview'];
        if (!validTabs.includes(tabId)) tabId = 'expenses';

        document.querySelectorAll('.tab, .tab-content').forEach(el => el.classList.remove('active'));
        const tabBtn = document.querySelector(`.tab[data-tab="${tabId}"]`);
        const tabContent = document.getElementById(`${tabId}-tab`);

        if (tabBtn) tabBtn.classList.add('active');
        if (tabContent) tabContent.classList.add('active');

        if (tabId === 'refunds' || tabId === 'overview' || tabId === 'invoices' || tabId === 'receipts' || tabId === 'payments') {
            loadCallback(tabId);
        }
    };

    // Router to handle hash changes
    const handleRoute = async () => {
        const hash = window.location.hash.slice(1) || 'expenses';
        const parts = hash.split('/');
        const route = parts[0];
        const id = parts[1];

        // Close any open modals first
        document.querySelectorAll('.modal.show').forEach(m => m.classList.remove('show'));

        // Handle deep links
        if (route === 'expense' && id) {
            activateTab('expenses');
            // Wait for data to load then open modal
            setTimeout(async () => {
                try {
                    const expense = store.expenses.find(e => e.id === parseInt(id));
                    if (expense) {
                        Renderers.renderExpenseDetailModal(expense);
                    } else {
                        showToast('Expense not found', 'error');
                    }
                } catch (err) { console.error(err); }
            }, 300);
        } else if (route === 'invoice' && id) {
            activateTab('invoices');
            setTimeout(async () => {
                try {
                    const data = await apiCall(`/invoices/details/${id}`);
                    Renderers.renderInvoiceDetailsModal(data);
                    document.getElementById('detailsModal').classList.add('show');
                } catch (err) { showToast('Invoice not found', 'error'); }
            }, 300);
        } else if (route === 'receipt' && id) {
            activateTab('receipts');
            setTimeout(async () => {
                try {
                    const data = await apiCall(`/receipts/details/${id}`);
                    Renderers.renderReceiptDetailsModal(data);
                    document.getElementById('detailsModal').classList.add('show');
                } catch (err) { showToast('Receipt not found', 'error'); }
            }, 300);
        } else if (route === 'refund' && id) {
            activateTab('refunds');
            setTimeout(async () => {
                try {
                    const data = await apiCall(`/refunds/${decodeURIComponent(id)}`);
                    Renderers.renderRefundDetail(data);
                } catch (err) { showToast('Refund data not found', 'error'); }
            }, 300);
        } else {
            // Simple tab navigation
            activateTab(route);
        }
    };

    // Handle tab clicks - update URL hash
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            window.location.hash = tab.dataset.tab;
        });
    });

    // Handle hash changes (back/forward buttons)
    window.addEventListener('hashchange', handleRoute);

    // Initial route
    handleRoute();
}

// Helper to update URL when opening detail modals
export function navigateTo(route) {
    window.location.hash = route;
}


export function setupForms(refreshCallback) {
    // Expense Form
    const expenseForm = document.getElementById('expenseForm');
    if (expenseForm) {
        expenseForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const checkedBoxes = document.querySelectorAll('#participantCheckboxes input:checked');
            const participantIds = Array.from(checkedBoxes).map(cb => parseInt(cb.value));

            if (participantIds.length === 0) return showToast('Select at least one participant', 'error');

            const data = {
                name: document.getElementById('expenseName').value,
                amount: parseFloat(document.getElementById('expenseAmount').value),
                currency: document.getElementById('expenseCurrency').value,
                buffer_rate: parseFloat(document.getElementById('bufferRate').value),
                participant_ids: participantIds
            };

            try {
                await apiCall('/expenses', { method: 'POST', body: JSON.stringify(data) });
                e.target.reset();
                document.querySelectorAll('.participant-checkbox').forEach(l => {
                    l.classList.remove('checked');
                    l.querySelector('input').checked = false;
                });
                refreshCallback('expenses');
                showToast('Expense added!', 'success');
            } catch (err) { showToast(err.message, 'error'); }
        });
    }

    // Toggle Participants (Select All)
    const toggleBtn = document.getElementById('toggleAllParticipants');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            const boxes = document.querySelectorAll('#participantCheckboxes input');
            const allChecked = Array.from(boxes).every(cb => cb.checked);
            boxes.forEach(cb => {
                cb.checked = !allChecked;
                cb.closest('.participant-checkbox').classList.toggle('checked', !allChecked);
            });
            toggleBtn.textContent = allChecked ? 'Select All' : 'Deselect All';
        });
    }

    // Individual Participant Checkbox Logic (Visual Toggle)
    const checkboxesContainer = document.getElementById('participantCheckboxes');
    if (checkboxesContainer) {
        checkboxesContainer.addEventListener('change', (e) => {
            if (e.target.tagName === 'INPUT' && e.target.type === 'checkbox') {
                const label = e.target.closest('.participant-checkbox');
                if (label) label.classList.toggle('checked', e.target.checked);
            }
        });
    }
}


export function setupGlobalDelegation(refreshCallback) {
    document.body.addEventListener('click', async (e) => {
        const btn = e.target.closest('button[data-action]');
        if (!btn) return;

        const action = btn.dataset.action;
        const id = btn.dataset.id;

        if (action === 'deleteParticipant') {
            if (!confirm('Delete participant?')) return;
            await apiCall(`/participants/${id}`, { method: 'DELETE' });
            refreshCallback('participants');
        } else if (action === 'deleteExpense') {
            if (!confirm('Delete expense?')) return;
            await apiCall(`/expenses/${id}`, { method: 'DELETE' });
            refreshCallback('expenses');
        } else if (action === 'viewExpense') {
            navigateTo(`expense/${id}`);
        } else if (action === 'logPaymentModal') {
            const expense = store.expenses.find(e => e.id === parseInt(id));
            if (expense) {
                document.getElementById('logPaymentExpenseId').value = expense.id;
                document.getElementById('logPaymentNameDisplay').value = expense.name;
                document.getElementById('logPaymentDate').value = new Date().toISOString().split('T')[0];
                document.getElementById('logPaymentAmount').value = expense.amount;
                document.getElementById('logPaymentCurrency').value = expense.currency;
                if (expense.currency === 'JPY') {
                    document.getElementById('logPaymentExchangeRate').value = expense.buffer_rate;
                    document.getElementById('logPaymentRateGroup').style.display = 'block';
                } else {
                    document.getElementById('logPaymentExchangeRate').value = 1;
                    document.getElementById('logPaymentRateGroup').style.display = 'none';
                }

                // Setup live THB preview calculation
                const updatePreview = () => {
                    const amount = parseFloat(document.getElementById('logPaymentAmount').value || 0);
                    const currency = document.getElementById('logPaymentCurrency').value;
                    const rate = parseFloat(document.getElementById('logPaymentExchangeRate').value || 0);
                    const previewEl = document.getElementById('logPaymentPreview');

                    if (currency === 'JPY' && rate > 0) {
                        const thb = amount * rate;
                        previewEl.innerHTML = `💱 Calculated THB: <strong>฿${thb.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</strong>`;
                    } else if (currency === 'THB') {
                        previewEl.innerHTML = `💱 Amount in THB: <strong>฿${amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</strong>`;
                    } else {
                        previewEl.innerHTML = '';
                    }
                };

                document.getElementById('logPaymentAmount').oninput = updatePreview;
                document.getElementById('logPaymentExchangeRate').oninput = updatePreview;
                document.getElementById('logPaymentCurrency').onchange = () => {
                    const cur = document.getElementById('logPaymentCurrency').value;
                    document.getElementById('logPaymentRateGroup').style.display = cur === 'JPY' ? 'block' : 'none';
                    updatePreview();
                };

                updatePreview(); // Initial calculation
                document.getElementById('logPaymentModal').classList.add('show');
            }
        } else if (action === 'deleteInvoice') {
            if (!confirm('Delete invoice? This will unlock associated expenses.')) return;
            await apiCall(`/invoices/${id}`, { method: 'DELETE' });
            refreshCallback('invoices'); // Refresh Invoices tab
        } else if (action === 'deleteReceipt') {
            if (!confirm('Void receipt? This will mark invoices as unpaid.')) return;
            await apiCall(`/receipts/${id}`, { method: 'DELETE' });
            refreshCallback('receipts'); // Refresh Receipts tab
        } else if (action === 'viewInvoice') {
            navigateTo(`invoice/${id}`);
        } else if (action === 'viewReceipt') {
            navigateTo(`receipt/${id}`);
        } else if (action === 'showRefundDetail') {
            const name = btn.dataset.name;
            navigateTo(`refund/${encodeURIComponent(name)}`);
        }
    });
}

export function setupModals(refreshCallback) {
    // Settings Modal
    const settingsBtn = document.getElementById('settingsBtn');
    const settingsModal = document.getElementById('settingsModal');
    if (settingsBtn && settingsModal) {
        settingsBtn.addEventListener('click', () => {
            document.getElementById('tripNameInput').value = store.settings.trip_name || '';
            document.getElementById('defaultRateInput').value = store.settings.default_buffer_rate || '';
            settingsModal.classList.add('show');
        });
        const closeBtn = document.getElementById('closeSettingsBtn');
        if (closeBtn) closeBtn.onclick = () => settingsModal.classList.remove('show');

        // Save Settings
        document.getElementById('saveSettingsBtn')?.addEventListener('click', async () => {
            const tripName = document.getElementById('tripNameInput').value;
            const defaultRate = parseFloat(document.getElementById('defaultRateInput').value);

            try {
                await apiCall('/settings', {
                    method: 'PUT', // Changed from POST to PUT to match original behavior
                    body: JSON.stringify({ trip_name: tripName, default_buffer_rate: defaultRate })
                });
                showToast('Settings saved!', 'success'); // Changed to showToast and added success
                document.getElementById('settingsModal').classList.remove('show'); // Changed from 'active' to 'show'
                refreshCallback('settings'); // Changed from 'all' to 'settings'
            } catch (err) {
                showToast(err.message, 'error');
            }
        });

        // Export Database
        document.getElementById('exportDbBtn')?.addEventListener('click', async () => {
            const btn = document.getElementById('exportDbBtn');
            const originalText = btn.textContent;
            btn.textContent = 'Exporting...';
            btn.disabled = true;

            try {
                const token = localStorage.getItem('adminToken');
                if (!token) {
                    showToast('Admin authentication required', 'error'); // Changed to showToast
                    return;
                }

                const response = await fetch('/api/export/db', {
                    headers: {
                        'X-Admin-Token': token
                    }
                });

                if (response.status === 401) {
                    showToast('Authentication failed. Please login.', 'error'); // Changed to showToast
                    return;
                }

                if (!response.ok) throw new Error('Export failed');

                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'trip_expenses_backup.zip';
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);

                showToast('Database exported successfully', 'success'); // Changed to showToast
            } catch (error) {
                console.error('Export error:', error);
                showToast('Failed to export database', 'error'); // Changed to showToast
            } finally {
                btn.textContent = originalText;
                btn.disabled = false;
            }
        });
        // Add Participant
        const addPartBtn = document.getElementById('addParticipantBtn');
        if (addPartBtn) {
            addPartBtn.onclick = async () => {
                const name = document.getElementById('newParticipantName').value;
                if (!name) return;
                try {
                    await apiCall('/participants', {
                        method: 'POST',
                        body: JSON.stringify({ name, total_paid: 0, total_owe: 0 })
                    });
                    document.getElementById('newParticipantName').value = '';
                    refreshCallback('participants');
                    showToast('Participant added', 'success');
                } catch (err) { showToast(err.message, 'error'); }
            };
        }
    }

    // Detail Modal Close
    const detailsModal = document.getElementById('detailsModal');
    if (detailsModal) {
        const closers = document.querySelectorAll('#closeDetailsBtn, #closeDetailsBtnFooter');

        const closeModal = () => {
            detailsModal.classList.remove('show');
            detailsModal.classList.remove('active');

            // Clear hash if it's a detail route
            const hash = window.location.hash;
            if (hash.match(/#(expense|invoice|receipt|refund)\//)) {
                const route = hash.slice(1).split('/')[0];
                const baseTab = (route === 'refund') ? 'refunds' : (route + 's');
                window.location.hash = baseTab;
            }
        };

        closers.forEach(btn => btn.onclick = closeModal);
        window.addEventListener('click', (e) => {
            if (e.target === detailsModal) closeModal();
        });
    }

    // Create Invoice Modal Logic
    const createInvoiceModal = document.getElementById('createInvoiceModal');
    const openCreateInvoiceBtn = document.getElementById('openCreateInvoiceModalBtn');
    if (createInvoiceModal && openCreateInvoiceBtn) {
        openCreateInvoiceBtn.onclick = () => {
            createInvoiceModal.classList.add('show');
            Renderers.renderCreateInvoiceModal(null, []); // Reset state
        };

        document.getElementById('closeCreateInvoiceModalBtn').onclick = () => createInvoiceModal.classList.remove('show');
        window.addEventListener('click', (e) => {
            if (e.target === createInvoiceModal) createInvoiceModal.classList.remove('show');
        });

        // Handle Participant Change
        const participantSelect = document.getElementById('createInvoiceParticipant');
        if (participantSelect) {
            participantSelect.addEventListener('change', async () => {
                const name = participantSelect.value;
                if (!name) {
                    Renderers.renderCreateInvoiceModal(null, []);
                    return;
                }
                try {
                    // Fetch unbilled expenses
                    // Use existing logic: GET /invoices/{name} which returns preview data (including new expenses)
                    // Or call /api/expenses?unbilled=true&participant={name} if implemented.
                    // The old logic called /invoices/{name}. Let's stick with that for now as it calculates shares.
                    const data = await apiCall(`/invoices/${name}`);
                    Renderers.renderCreateInvoiceModal(name, data.new_expenses || []);
                } catch (err) { showToast(err.message, 'error'); }
            });
        }

        // Handle Generate
        const generateBtn = document.getElementById('doGenerateInvoiceBtn');
        if (generateBtn) {
            generateBtn.onclick = async () => {
                const name = document.getElementById('createInvoiceParticipant').value;
                const checked = document.querySelectorAll('.create-invoice-check:checked');
                const expenseIds = Array.from(checked).map(cb => parseInt(cb.value));

                if (!name) return;
                try {
                    await apiCall(`/invoices/${name}/generate`, {
                        method: 'POST',
                        body: JSON.stringify({ expense_ids: expenseIds })
                    });
                    showToast('Invoice generated!', 'success');
                    createInvoiceModal.classList.remove('show');
                    refreshCallback('invoices');
                } catch (err) { showToast(err.message, 'error'); }
            };
        }
    }

    // Create Receipt Modal Logic
    const createReceiptModal = document.getElementById('createReceiptModal');
    const openCreateReceiptBtn = document.getElementById('openCreateReceiptModalBtn');
    if (createReceiptModal && openCreateReceiptBtn) {
        openCreateReceiptBtn.onclick = () => {
            createReceiptModal.classList.add('show');
            Renderers.renderCreateReceiptModal(null, []);
        };

        document.getElementById('closeCreateReceiptModalBtn').onclick = () => createReceiptModal.classList.remove('show');
        window.addEventListener('click', (e) => {
            if (e.target === createReceiptModal) createReceiptModal.classList.remove('show');
        });

        // Handle Participant Change
        const participantSelect = document.getElementById('createReceiptParticipant');
        if (participantSelect) {
            participantSelect.addEventListener('change', async () => {
                const name = participantSelect.value;
                if (!name) {
                    Renderers.renderCreateReceiptModal(null, []);
                    return;
                }
                try {
                    // Fetch receipt preview (unpaid invoices)
                    const data = await apiCall(`/receipts/${name}`);
                    Renderers.renderCreateReceiptModal(name, data.unpaid_invoices || []);
                } catch (err) { showToast(err.message, 'error'); }
            });
        }

        // Handle Generate
        const generateBtn = document.getElementById('doGenerateReceiptBtn');
        if (generateBtn) {
            generateBtn.onclick = async () => {
                const name = document.getElementById('createReceiptParticipant').value;
                const checked = document.querySelectorAll('.create-receipt-check:checked');
                const invoiceIds = Array.from(checked).map(cb => parseInt(cb.value));
                const method = document.getElementById('createReceiptMethod').value;

                if (!name) return;

                try {
                    await apiCall(`/receipts/${name}/generate`, {
                        method: 'POST',
                        body: JSON.stringify({ payment_method: method, invoice_ids: invoiceIds })
                    });
                    showToast('Receipt generated!', 'success');
                    createReceiptModal.classList.remove('show');
                    refreshCallback('receipts');
                } catch (err) { showToast(err.message, 'error'); }
            };
        }
    }

    // Log Payment Modal
    const logPaymentModal = document.getElementById('logPaymentModal');
    if (logPaymentModal) {
        const closeBtn = document.getElementById('closeLogPaymentBtn');
        if (closeBtn) closeBtn.onclick = () => logPaymentModal.classList.remove('show');
        window.addEventListener('click', (e) => {
            if (e.target === logPaymentModal) logPaymentModal.classList.remove('show');
        });

        const savePayBtn = document.getElementById('savePaymentBtn');

        if (savePayBtn) {
            savePayBtn.onclick = async (e) => {
                e.preventDefault();
                const expId = document.getElementById('logPaymentExpenseId').value;
                const date = document.getElementById('logPaymentDate').value;
                const method = document.getElementById('logPaymentMethod').value;
                const amount = parseFloat(document.getElementById('logPaymentAmount').value);
                const currency = document.getElementById('logPaymentCurrency').value;
                const rate = parseFloat(document.getElementById('logPaymentExchangeRate').value || 1);

                if (!amount) return showToast('Enter amount', 'error');
                if (!date) return showToast('Enter date', 'error');

                const actualThb = currency === 'JPY' ? amount * rate : amount;

                const payload = {
                    date: date,
                    method: method,
                    actual_amount: amount,
                    actual_currency: currency,
                    actual_thb: actualThb
                };

                try {
                    await apiCall(`/expenses/${expId}/payment`, { method: 'POST', body: JSON.stringify(payload) });
                    logPaymentModal.classList.remove('show');
                    refreshCallback('expenses');
                    showToast('Payment logged successfully!', 'success');
                } catch (err) { showToast(err.message, 'error'); }
            };
        }
    }
}
