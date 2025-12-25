import { apiCall, setTripId } from './client_api.js';
import * as Store from './store.js';
import * as Renderers from './renderers.js';
import * as UI from './ui.js';
import { isAdmin, logout, setToken, validateToken, applyAuthRestrictions, verifyStoredToken } from './auth.js';

async function loadData(type = 'all') {
    try {
        if (type === 'all' || type === 'settings') {
            const settings = await apiCall('/settings');
            Store.setSettings(settings);
            document.getElementById('tripName').textContent = settings.trip_name;
            // Update page title
            document.title = `${settings.trip_name} - Nine Travel`;
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
            // Fetch overview data
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

// === Landing Page Logic ===
function setupLandingPage() {
    const joinBtn = document.getElementById('joinTripBtn');
    const linkInput = document.getElementById('tripLinkInput');

    joinBtn?.addEventListener('click', () => {
        const input = linkInput.value.trim();
        if (!input) return;

        // Extract ID from URL
        // Support full URL or just ID
        // URL pattern: .../t/{id}
        let tripId = input;

        // Simple regex to find /t/UUID
        const match = input.match(/\/t\/([a-zA-Z0-9-]+)/);
        if (match) {
            tripId = match[1];
        }

        if (tripId) {
            window.location.href = `/t/${tripId}`;
        } else {
            alert("Invalid link format.");
        }
    });
}

async function initApp(tripId) {
    setTripId(tripId);

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

    // Share Button Logic
    document.getElementById('shareTripBtn')?.addEventListener('click', () => {
        navigator.clipboard.writeText(window.location.href);
        UI.showToast('Trip link copied to clipboard!', 'success');
    });

    // Show app, hide landing
    document.getElementById('landingPage').classList.remove('active');
    document.getElementById('mainApp').style.display = 'block';

    // Hide Loader
    setTimeout(() => {
        const loader = document.getElementById('globalLoader');
        if (loader) loader.classList.remove('active');
    }, 500);
}

function handleRouting() {
    const path = window.location.pathname;
    const match = path.match(/^\/t\/([a-zA-Z0-9-]+)/);

    if (match) {
        // We have a trip ID
        const tripId = match[1];
        initApp(tripId);
    } else if (path === '/admin') {
        // Admin Dashboard
        document.getElementById('globalLoader').classList.remove('active');
        document.getElementById('landingPage').classList.remove('active');
        document.getElementById('mainApp').style.display = 'none';
        document.getElementById('adminPage').classList.remove('hidden');

        loadAdminDashboard();
    } else {
        // Show Landing Page
        document.getElementById('globalLoader').classList.remove('active');
        document.getElementById('landingPage').classList.add('active');
        document.getElementById('mainApp').style.display = 'none';
        setupLandingPage();
    }
}

async function loadAdminDashboard() {
    // Check if logged in
    if (!isAdmin()) {
        const token = prompt("Admin Access Required. Please enter Admin Token:");
        if (token) {
            const isValid = await validateToken(token);
            if (isValid) {
                setToken(token);
            } else {
                alert("Invalid Token");
                window.location.href = '/';
                return;
            }
        } else {
            window.location.href = '/';
            return;
        }
    }

    // Setup Create Trip button on admin page (do this first)
    const createBtn = document.getElementById('createTripBtn');
    if (createBtn) {
        createBtn.addEventListener('click', async () => {
            const name = prompt("Enter a name for your trip:");
            if (!name) return;

            createBtn.textContent = "Creating...";
            createBtn.disabled = true;

            try {
                const res = await apiCall('/trips', {
                    method: 'POST',
                    body: JSON.stringify({ name })
                });

                if (res.id) {
                    UI.showToast(`Trip "${name}" created!`, 'success');
                    // Reload dashboard to show new trip
                    const newStats = await apiCall('/trips/admin/dashboard');
                    Renderers.renderAdminDashboard(newStats);
                }
            } catch (e) {
                alert("Error creating trip: " + e.message);
            } finally {
                createBtn.textContent = "🚀 Create New Trip";
                createBtn.disabled = false;
            }
        });
    }

    // Load dashboard data
    try {
        const stats = await apiCall('/trips/admin/dashboard');
        Renderers.renderAdminDashboard(stats);
    } catch (err) {
        console.error("Failed to load admin dashboard", err);
        UI.showToast("Failed to load admin data", "error");
    }
}

document.addEventListener('DOMContentLoaded', () => {
    handleRouting();
});

