# 🧳 Trip Expense Manager

A modern web application for managing group travel expenses with currency conversion, PDF invoice generation, and refund reconciliation.

**Developed by Nine Travel Co., Ltd.**

## Features

- **💰 Expense Tracking**: Add shared expenses with multiple currencies (THB, JPY) and buffer rates
- **👥 Participant Management**: Track expenses per participant with equal split calculations
- **📄 Invoice Generation**: Generate professional PDF invoices with version history
- **🧾 Receipt System**: Record payments and generate payment receipts
- **💸 Refund Reconciliation**: Automatically calculate refunds based on actual vs. collected amounts
- **💱 Exchange Rate Support**: Live THB calculation when logging actual payments

## Tech Stack

- **Backend**: Python FastAPI
- **Frontend**: Vanilla JavaScript with ES Modules
- **Database**: SQLite
- **PDF Generation**: ReportLab with Thai font support (Sarabun)
- **Styling**: Custom CSS with modern dark theme

## Quick Start

### Prerequisites

- Python 3.8+
- pip

### Installation

```bash
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Run the server
python -m uvicorn main:app --reload --port 8000
```

### Access the Application

Open [http://localhost:8000](http://localhost:8000) in your browser.

## Project Structure

```
trip-expense-manager/
├── backend/
│   ├── data/
│   │   ├── fonts/          # Thai fonts for PDF
│   │   └── pdfs/           # Generated PDFs (gitignored)
│   ├── routes/
│   │   ├── expenses.py     # Expense CRUD operations
│   │   ├── invoices.py     # Invoice generation
│   │   ├── receipts.py     # Receipt handling
│   │   ├── refunds.py      # Refund reconciliation
│   │   ├── participants.py # Participant management
│   │   └── settings.py     # App settings
│   ├── static/
│   │   ├── js/             # Frontend JavaScript modules
│   │   ├── index.html      # Main HTML page
│   │   └── styles.css      # Application styles
│   ├── database.py         # SQLite database operations
│   ├── schemas.py          # Pydantic models
│   ├── pdf_generator.py    # PDF generation logic
│   └── main.py             # FastAPI application
└── README.md
```

## Usage

### Managing Expenses

1. Add participants in the Settings modal
2. Create expenses with amount, currency, and participant selection
3. View expense details by clicking on any expense card

### Generating Invoices

1. Go to **Invoices** tab
2. Click **Generate Invoice** for a participant
3. Select expenses to include
4. Download the generated PDF

### Logging Payments

1. Click **Log Payment** on any expense
2. Enter actual amount paid and exchange rate
3. System calculates THB automatically

### Processing Refunds

1. Go to **Refunds** tab
2. View reconciliation summary per participant
3. Click **Details** to see breakdown
4. Download refund statement PDF

## License

© 2025 Nine Travel Co., Ltd. All rights reserved.
