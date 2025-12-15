export function formatCurrency(amount, currency) {
    const symbol = currency === 'JPY' ? '¥' : '฿';
    if (amount === undefined || amount === null) return '-';
    return `${symbol}${amount.toLocaleString()}`;
}

export function formatDate(dateStr) {
    if (!dateStr) return '-';
    return dateStr.split('T')[0];
}
