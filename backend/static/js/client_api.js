import { getToken } from './auth.js';

const API_BASE = '/api';

let currentTripId = null;

export function setTripId(id) {
    currentTripId = id;
}

export function getTripId() {
    return currentTripId;
}

export async function apiCall(endpoint, options = {}) {
    try {
        const token = getToken();
        const headers = {
            'Content-Type': 'application/json',
            ...(token && { 'X-Admin-Token': token }),
            ...(currentTripId && { 'X-Trip-ID': currentTripId }),
            ...options.headers
        };

        const response = await fetch(`${API_BASE}${endpoint}`, {
            ...options,
            headers
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'API Error');
        }

        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

export { API_BASE };
