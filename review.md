# Trip Expense Manager - Application Review

## 🚨 Critical Issues (Fixed in this update)

1.  **Database Integrity**: Foreign Key support was disabled in SQLite by default.
    *   *Issue*: Deleting a participant would leave orphaned expense records, corrupting data.
    *   *Fix*: Enabled `PRAGMA foreign_keys = ON`.
2.  **PDF Font Support**: Default fonts do not support Thai/Japanese characters.
    *   *Issue*: Generated PDFs would show "□□□" instead of names like "Nine" (if in Thai) or "Tokyo".
    *   *Fix*: Integrated `Sarabun` font for full unicode (Thai) support.

## 🛠 UI/UX Improvements (Included in this update)

3.  **Loading State**: Users saw a broken/empty page while data loaded.
    *   *Fix*: Added a professional full-screen loading overlay during initialization.
4.  **Bulk Selection**: Selecting 10 participants one by one is tedious.
    *   *Fix*: Added "Select All / Deselect All" toggle for creating new expenses.
5.  **Navigation Feedback**: Added visual feedback (toasts) is good, but added loaders for specific actions.

## 💡 Logic & Flow Suggestions (Recommended for future)

6.  **Expense Validation**:
    *   Currently, you can enter an expense with amount `0` or negative.
    *   *Suggestion*: Add validation schema in backend (Pydantic) and frontend constraints.
7.  **Exchange Rate Sanity Check**:
    *   Entering `23` instead of `0.23` for JPY rate throws off calculations massively.
    *   *Suggestion*: Warn user if rate deviates >10% from standard range (0.20-0.25).
8.  **Participant Management**:
    *   "Nine", "Nam", etc. are hardcoded in `init_db`.
    *   *Suggestion*: Remove hardcoding. Allow full CRUD management of participants from a "Settings" tab.
9.  **Partial Payments**:
    *   Logging actuals assumes one payment or multiple distinct payments.
    *   *Suggestion*: Group related actuals by expense in the "Actuals" view.
10. **Currency Support**:
    *   Hardcoded `JPY` and `THB`.
    *   *Suggestion*: Create a `Currencies` table to support SG, KR, VN trips.

## 🏗 Code & Architecture

11. **API Structure**:
    *   `routes/` folder is good.
    *   *Optimization*: Use a dependency injection for `get_db` to make unit testing easier.
12. **Frontend Architecture**:
    *   `app.js` is becoming monolithic (~1000 lines).
    *   *Suggestion*: Refactor into modules (`api.js`, `ui.js`, `utils.js`) using ES6 modules.
