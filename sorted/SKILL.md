---
name: sorted
description: Automate getSorted.de (Sorted) for freelancer invoicing, expense tracking, and German tax submissions (VAT, ZM, annual returns). Uses real-browser automation via Chrome Beta + agent-browser. Triggers on "create invoice", "sorted invoice", "download invoice", "submit VAT", "tax report", "sorted expenses", "/sorted", or any getSorted.de interaction.
---

# Sorted — Freelancer Tax & Invoicing Automation

Automates [getSorted.de](https://app.getsorted.de/) via real Chrome Beta browser for invoicing, expense tracking, and German tax report submissions.

## Prerequisites

- Chrome Beta with `--remote-debugging-port=9222` (use `/real-browser` launch sequence)
- Google account session persisted in `~/.chrome-beta-profile`
- `agent-browser` CLI installed

## Commands

### `invoice create`

Create a new invoice on Sorted.

**Required params:** client name, amount
**Optional:** hours, rate, description, due date, service date, client type (business/person)

### `invoice download <invoice-number>`

Download a properly formatted PDF from Sorted (not browser print).

### `invoice send <invoice-number> --email <email>`

Send invoice via email directly from Sorted (paid plan only). On free plan, downloads PDF and sends via Telegram instead.

### `invoice list`

List all invoices with status (paid/unpaid).

### `expense add`

Add an expense entry.

### `tax status`

Show current tax obligations, deadlines, and overdue reports.

### `tax preview <report-type> <period>`

Preview a tax report before submission.

### `tax submit <report-type> <period>`

Submit a tax report to Finanzamt via ELSTER (requires paid plan).

## Sorted Navigation

App URL: `https://app.getsorted.de/`

| Section | Sidebar link | Purpose |
|---------|-------------|---------|
| Dashboard | Sorted (logo) | Overview: taxes owed, income, expenses |
| Taxes | Taxes | Tax reports, deadlines, submissions |
| Income | Income | Invoice list, create/edit invoices |
| Expenses | Expenses | Expense tracking, receipts |
| Tax consultant | Tax consultant | Advisor connection |
| Personal details | Profile → Personal details | Freelancer info, Steuernummer |
| Bank accounts | Profile → Bank accounts (Beta) | Connected banks |
| Subscription | Profile → Subscription | Plan management |
| Import | Profile → Import your data | Bulk data import |
| Settings | Profile → Settings | App preferences |

## Tax Report Types

| Report | German name | Frequency | Description |
|--------|------------|-----------|-------------|
| Advance VAT | Umsatzsteuer-Voranmeldung (UStVA) | Quarterly | VAT collected on invoices |
| EU Summary | Zusammenfassende Meldung (ZM) | Quarterly | Revenue from EU customers |
| Annual Returns | EÜR + Einkommensteuererklärung | Yearly | Profit/loss + income tax |

## Invoice Creation Flow

### Step-by-step browser automation:

1. **Navigate:** `Income` → click `Add` → `Create invoice`
2. **Set client:** Click `Client details` area on invoice preview
   - Search existing clients or click `Add new client`
   - Choose `Business` or `Private person`
   - Fill: name, VAT/TIN, street, city, zip, country (autocomplete dropdown — type then click match), email (optional)
   - Click `Save` in dialog
3. **Set invoice date:** Click the date next to "Invoice date" (defaults to today)
4. **Set service date (REQUIRED):** Click the empty area to the right of invoice date labeled "Service date"
   - This is a **date range picker** — select start date, then end date
   - If same-day service, click the same date twice
   - **Without service date, Save will fail silently** — the field shows "Required" in red
   - The clickable element has class `clickable` and is positioned at ~x:734 y:413 on the invoice preview
   - If snapshot doesn't show it, use JS: find div with text "Service dateRequired" and click it
5. **Set due date:** Click "Select date" under "Due date" → pick from calendar
6. **Add line item:** Click `Add a line`
   - Fields: description (text), quantity (number), unit dropdown (h/pcs/etc), rate (number)
   - Click on collapsed values to re-edit them
7. **VAT:** Automatically 0% for Kleinunternehmer accounts. Shows "Service not taxable in Germany" in notes
8. **Save:** Click `Save` button. Title changes from "Add invoice" to "Edit invoice" on success

### Gotchas

- **Service date is mandatory** but easy to miss — it's not highlighted until you try to save
- **German number formatting:** dots are thousands separators (1.000 = one thousand), commas are decimals
- **Collapsed fields:** After saving, line item fields collapse to display-only. Click the displayed value to re-open the editable field
- **Invoice number:** Auto-generated sequentially (e.g., 2025-03-21). Can be edited by clicking it

## Invoice PDF Download Flow

**CRITICAL: Do NOT use Chrome CDP `Page.printToPDF` — it captures the entire page including sidebar and settings panel. Always use Sorted's native PDF.**

### Step-by-step:

1. Open the invoice (click from Income list, or navigate after creating)
2. Click `Save and send` button (top right, teal button)
3. An **"Email invoice"** dialog appears with:
   - To field (email)
   - Subject (auto-filled)
   - Message textarea
   - **Attachments section** at the bottom showing the PDF filename
4. Click the PDF link (e.g., `ALL3 DOO BELGRADE-2025-03-21-20260506.pdf`)
   - It's a `generic` element with `cursor:pointer` and `onclick`
   - The text matches pattern: `{CLIENT_NAME}-{INVOICE_NUMBER}-{DATE}.pdf`
5. PDF downloads to `~/Downloads/`
6. Close the dialog (click `Close` or `×`)

### Email sending (paid plan)

On paid plans, the "Email invoice" dialog is fully functional:

1. Fill `To` field with client email (`@e49`)
2. Edit `Subject` if needed (auto-filled as "Gleb Kalinin sent you an invoice (#INVOICE-NUMBER)")
3. Write a `Message` in the textarea
4. Toggle "Send a copy to my email" checkbox (checked by default)
5. Click `Email invoice` button (`@e15`) to send

On the **free plan**, the dialog shows "Sending invoices by email is not available in your plan" with a "Change my plan" link. The PDF download still works regardless.

### Fallback: Telegram delivery (free plan)

When email sending is unavailable, download the PDF and send via Telethon (see "Sending Invoice After Download" section below).

### PDF filename pattern
```
{CLIENT_NAME}-{INVOICE_NUMBER}-{YYYYMMDD}.pdf
```
Example: `ALL3 DOO BELGRADE-2025-03-21-20260506.pdf`

## Client Management

Existing clients are stored and reusable. When creating an invoice:
- The client picker shows all saved clients
- Search by name in the search box
- Edit/delete clients via small buttons next to each name

### Client fields (Business)
- Business name (required)
- VAT number / TIN (optional)
- Street & Number
- City
- Zip Code
- Country (autocomplete — type and click match)
- Email

### Client fields (Private person)
- First name, Last name
- Address fields same as business

## Sending Invoice After Download

After downloading the PDF, send via Telegram using Telethon:

```python
from telethon.sync import TelegramClient
import json
from pathlib import Path

config = json.loads((Path.home() / '.telegram_dl' / 'config.json').read_text())
session = str(Path.home() / '.telegram_dl' / 'user')

with TelegramClient(session, config['api_id'], config['api_hash']) as client:
    client.send_file("username", "/path/to/invoice.pdf", caption="message")
```

## Gleb's Sorted Account Details

- **Status:** Kleinunternehmer (no VAT charged)
- **Finanzamt:** Berlin - Wedding
- **VAT-ID:** DE369692682
- **Tax Number:** 2337201265
- **Bank:** Revolut Bank UAB, Zweigniederlassung
- **IBAN:** DE38 1001 0178 8157 1777 30
- **BIC/SWIFT:** REVODEB2
- **Plan:** Free (invoicing works, tax submission requires upgrade)

## Browser Session Setup

Always use the `/real-browser` skill's launch sequence. Session name should be unique per run:

```bash
SESSION=$(LC_ALL=C tr -dc 'a-z0-9' < /dev/urandom | head -c 6)
agent-browser --cdp 9222 --session "$SESSION" open "https://app.getsorted.de/"
```

Google login is persisted — no need to re-authenticate each time.
