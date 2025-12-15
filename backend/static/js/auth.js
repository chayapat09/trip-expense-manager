/**
 * Simple Token Authentication Module for Trip Expense Manager
 * Handles login/logout and token management
 */

const TOKEN_KEY = 'adminToken';

/**
 * Check if user is authenticated as admin
 */
export function isAdmin() {
    return !!localStorage.getItem(TOKEN_KEY);
}

/**
 * Get stored token
 */
export function getToken() {
    return localStorage.getItem(TOKEN_KEY);
}

/**
 * Store token after successful login
 */
export function setToken(token) {
    localStorage.setItem(TOKEN_KEY, token);
}

/**
 * Clear token on logout
 */
export function logout() {
    localStorage.removeItem(TOKEN_KEY);
    window.location.reload();
}

/**
 * Validate token with backend
 */
export async function validateToken(token) {
    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token })
        });
        return response.ok;
    } catch {
        return false;
    }
}

/**
 * Verify existing token is still valid
 */
export async function verifyStoredToken() {
    const token = getToken();
    if (!token) return false;

    try {
        const response = await fetch('/api/auth/verify', {
            method: 'POST',
            headers: { 'X-Admin-Token': token }
        });
        const data = await response.json();
        if (!data.valid) {
            // Clear invalid token
            localStorage.removeItem(TOKEN_KEY);
        }
        return data.valid;
    } catch {
        return false;
    }
}

/**
 * Apply UI restrictions based on auth state
 */
export function applyAuthRestrictions() {
    const isAuthenticated = isAdmin();
    document.body.classList.toggle('guest-mode', !isAuthenticated);
    updateAuthButton(isAuthenticated);
}

/**
 * Update auth button appearance
 */
function updateAuthButton(isAuthenticated) {
    const authBtn = document.getElementById('authBtn');
    if (!authBtn) return;

    if (isAuthenticated) {
        authBtn.innerHTML = '🔓 Logout';
        authBtn.classList.remove('btn-login');
        authBtn.classList.add('btn-logout');
        authBtn.title = 'Logout from admin mode';
    } else {
        authBtn.innerHTML = '🔒 Login';
        authBtn.classList.remove('btn-logout');
        authBtn.classList.add('btn-login');
        authBtn.title = 'Login as admin';
    }
}
