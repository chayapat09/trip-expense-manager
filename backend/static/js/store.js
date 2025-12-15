export const store = {
    participants: [],
    expenses: [],
    actuals: [],
    settings: {}
};

export function setParticipants(data) { store.participants = data; }
export function setExpenses(data) { store.expenses = data; }
export function setActuals(data) { store.actuals = data; }
export function setSettings(data) { store.settings = data; }
