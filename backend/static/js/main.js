import { apiCall } from './api.js';
import * as Store from './store.js';
import * as Renderers from './renderers.js?v=6';
import * as UI from './ui.js?v=4';

async function loadData(type = 'all') {
    try {
        if (type === 'all' || type === 'settings') {
            const settings = await apiCall('/settings');
            Store.setSettings(settings);
            document.getElementById('tripName').textContent = settings.trip_name;
        }
        if (type === 'all' || type === 'participants') {
            const parts = await apiCall('/participants');
            Store.setParticipants(parts);
            Renderers.renderParticipantCheckboxes();
            Renderers.renderParticipantsList();
            Renderers.renderParticipantSelects();
        }
        if (type === 'all' || type === 'expenses') {
            const exps = await apiCall('/expenses');
            Store.setExpenses(exps);
            Renderers.renderExpensesTable();
        }

        if (type === 'overview') {
            const data = await apiCall('/invoices/overview/all');
            Renderers.renderOverview(data);
        }
        if (type === 'invoices') {
            const data = await apiCall('/invoices');
            Renderers.renderInvoicesTab(data);
        }
        if (type === 'receipts') {
            const data = await apiCall('/receipts/');
            Renderers.renderReceiptsTab(data);
        }
        if (type === 'refunds') {
            const data = await apiCall('/refunds/reconciliation');
            Renderers.renderReconciliationTable(data);
        }
    } catch (error) {
        console.error('Load Error', error);
        UI.showToast('Failed to load data', 'error');
    }
}

document.addEventListener('DOMContentLoaded', async () => {
    // Initial Load
    await loadData('all');

    // Setup UI with Refresh Callback
    UI.setupTabs(loadData);
    UI.setupForms(loadData);
    UI.setupModals(loadData);
    UI.setupGlobalDelegation(loadData);

    // Hide Loader
    setTimeout(() => {
        const loader = document.getElementById('globalLoader');
        if (loader) loader.classList.remove('active');
    }, 500);
});
