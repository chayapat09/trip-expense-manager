import { apiCall } from './api.js';
import * as Store from './store.js';
import * as Renderers from './renderers.js?v=8';
import * as UI from './ui.js?v=6';
import { isAdmin, logout, setToken, validateToken, applyAuthRestrictions, verifyStoredToken } from './auth.js';

async function loadData(type = 'all') {
    try {
        if (type === 'all' || type === 'settings') {
            const settings = await apiCall('/settings');
            Store.setSettings(settings);
            document.getElementById('tripName').textContent = settings.trip_name;
            const bufferInput = document.getElementById('bufferRate');
            if (bufferInput) bufferInput.value = settings.default_buffer_rate || 0.25;
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
        if (type === 'payments') {
            // Re-fetch expenses to get latest payment status
            const exps = await apiCall('/expenses');
            Store.setExpenses(exps);
            Renderers.renderPaymentsTab(exps);
        }
    } catch (error) {
        console.error('Load Error', error);
        UI.showToast('Failed to load data', 'error');
    }
}

/**
 * Setup authentication handlers for login modal and logout
 */
function setupAuthHandlers() {
    const authBtn = document.getElementById('authBtn');
    const loginModal = document.getElementById('loginModal');
    const closeLoginBtn = document.getElementById('closeLoginBtn');
    const doLoginBtn = document.getElementById('doLoginBtn');
    const tokenInput = document.getElementById('adminTokenInput');
    const loginError = document.getElementById('loginError');

    // Auth button click - toggle login/logout
    authBtn?.addEventListener('click', () => {
        if (isAdmin()) {
            if (confirm('Are you sure you want to logout?')) {
                logout();
            }
        } else {
            loginModal.classList.add('active');
            tokenInput.value = '';
            loginError.style.display = 'none';
            setTimeout(() => tokenInput.focus(), 100);
        }
    });

    // Close login modal
    closeLoginBtn?.addEventListener('click', () => {
        loginModal.classList.remove('active');
    });

    // Close modal on background click
    loginModal?.addEventListener('click', (e) => {
        if (e.target === loginModal) {
            loginModal.classList.remove('active');
        }
    });

    // Login attempt
    doLoginBtn?.addEventListener('click', async () => {
        const token = tokenInput.value.trim();
        if (!token) {
            tokenInput.focus();
            return;
        }

        doLoginBtn.disabled = true;
        doLoginBtn.textContent = 'Logging in...';

        const isValid = await validateToken(token);

        if (isValid) {
            setToken(token);
            loginModal.classList.remove('active');
            UI.showToast('Login successful! Reloading...', 'success');
            setTimeout(() => window.location.reload(), 500);
        } else {
            loginError.style.display = 'block';
            tokenInput.value = '';
            tokenInput.focus();
            doLoginBtn.disabled = false;
            doLoginBtn.textContent = 'Login';
        }
    });

    // Enter key to submit login
    tokenInput?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            doLoginBtn.click();
        }
    });
}

document.addEventListener('DOMContentLoaded', async () => {
    // Verify stored token on page load
    await verifyStoredToken();

    // Apply UI restrictions based on auth state
    applyAuthRestrictions();

    // Initial Load
    await loadData('all');

    // Setup UI with Refresh Callback
    UI.setupTabs(loadData);
    UI.setupForms(loadData);
    UI.setupModals(loadData);
    UI.setupGlobalDelegation(loadData);

    // Setup auth handlers
    setupAuthHandlers();

    // Hide Loader
    setTimeout(() => {
        const loader = document.getElementById('globalLoader');
        if (loader) loader.classList.remove('active');
    }, 500);
});

