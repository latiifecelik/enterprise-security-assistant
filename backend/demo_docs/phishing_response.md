# Phishing Incident Response Guide

## Overview

Phishing is one of the most common initial access vectors in cybersecurity incidents.
This guide provides SOC analysts with structured procedures for identifying, investigating,
and responding to phishing attacks and their downstream consequences.

---

## 1. Types of Phishing

### Phishing
Mass-targeted email campaigns that impersonate legitimate organisations
(banks, services, IT departments) to steal credentials or deliver malware.
Not targeted to specific individuals.

### Spear Phishing
Targeted phishing directed at specific individuals or organisations. The attacker
researches the target to make the email convincing. Often used in APT campaigns.

### Whaling
Spear phishing directed specifically at high-value targets such as executives (CEO,
CFO, CISO). May be used for Business Email Compromise (BEC).

### Vishing (Voice Phishing)
Social engineering via phone calls. Attacker impersonates IT support, bank, or
government agency.

### Smishing (SMS Phishing)
Phishing via SMS messages, often with malicious links or urgent requests.

---

## 2. Phishing Indicators

### Email-Level Indicators

**Header Anomalies:**
- `From` address does not match `Reply-To`
- Sending domain does not match the displayed name (e.g., "Microsoft Support" from `@gmail.com`)
- SPF, DKIM, or DMARC failures
- Unusual mail relay hops

**Content Indicators:**
- Urgency language ("Your account will be suspended in 24 hours!")
- Grammar and spelling errors (though sophisticated attacks may be well-written)
- Generic salutations ("Dear Customer" instead of the recipient's name)
- Requests for credentials, payment, or sensitive information
- Links that hover-reveal a different URL than displayed

**Link Indicators:**
- Domain name typosquatting (e.g., `microsoft-support.com`, `paypa1.com`)
- Redirectors or URL shorteners masking the final destination
- HTTPS certificate on an untrusted or recently-registered domain
- URL containing IP address instead of domain name

**Attachment Indicators:**
- Macro-enabled Office documents (.xlsm, .xlsb, .docm)
- Password-protected archives (evades email scanning)
- Double-extension files (e.g., `invoice.pdf.exe`)
- HTML attachments (used for credential harvesting locally)

---

## 3. Phishing Investigation Procedure

### Phase 1: Triage the Report

1. **Obtain the original email** in raw format (.eml or message headers)
   - Request from the user or extract from email gateway quarantine
   - Do NOT open attachments or click links during triage

2. **Analyse email headers**
   - Examine `Received` headers to trace the email path
   - Check SPF, DKIM, DMARC authentication results
   - Identify the originating mail server IP

3. **Examine the sender**
   - Is the From address from a legitimate domain?
   - Has this sender sent legitimate email previously?
   - Is the sender's domain recently registered?

4. **Assess the payload**
   - If a link: Extract the URL without clicking — use URLScan.io or VirusTotal
   - If an attachment: Hash the file and check against VirusTotal
   - Identify whether a credential harvesting page, malware, or exploit is involved

### Phase 2: Scope the Impact

1. **Identify all recipients**
   - How many users received this email?
   - Was it sent to a distribution list or targeted individuals?

2. **Identify users who interacted**
   - Email gateway click-tracking (if available)
   - Web proxy logs: Did any user visit the phishing URL?
   - Endpoint logs: Was any attachment opened?

3. **Identify users who submitted credentials**
   - Review proxy logs for POST requests to the phishing domain
   - Look for authentication events from accounts that received the email
   - Check for logins from unusual locations/times following the campaign

### Phase 3: Contain the Threat

1. **Block the phishing infrastructure**
   - Add the phishing domain and IP to email gateway blocklist
   - Add to web proxy/DNS blocklist
   - Add to endpoint security blocklist

2. **Quarantine the email**
   - Remove the phishing email from all mailboxes
   - Use email administrator tools (Exchange Admin Center, M365 Defender, etc.)

3. **Contain affected accounts**
   - Reset passwords for accounts that submitted credentials
   - Revoke active sessions and tokens
   - Enforce MFA on affected accounts
   - Review and remove any email rules or forwarding set up by the attacker

4. **Contain affected endpoints**
   - If malware was executed, isolate the endpoint
   - Run EDR scan and collect forensic artefacts

---

## 4. Evidence to Collect

### From the Email System
- Raw email (with all headers) in .eml format
- Email metadata: sender, recipients, timestamp, message ID
- Email gateway logs (MX records, routing, scanning results)
- List of all recipients and whether they opened/clicked

### From the Web Proxy
- All HTTP/HTTPS requests to the phishing domain by affected users
- Any POST requests (indicating credential submission)
- File downloads from the phishing infrastructure

### From Endpoints
- Browser history and cached files
- Downloads folder contents
- Process execution logs (EDR)
- Network connections made by any executed payload

### From Identity Systems
- Authentication logs for affected accounts during and after the campaign
- Changes to account settings (forwarding rules, recovery addresses, MFA devices)
- Privilege escalation events if account was compromised

---

## 5. Post-Incident Actions

### Immediate
- Notify affected users that their credentials may be compromised
- Enforce password reset for all users who interacted with the phish
- Brief the security leadership team on scope and impact

### Short-Term
- Review email gateway configuration — could DMARC enforcement have blocked this?
- Review web proxy policies — was the domain categorised and blocked?
- Consider adding the phishing domain to threat intelligence sharing platforms

### Long-Term
- Use the phishing email as content for a simulated phishing awareness campaign
- Review phishing simulation metrics — are certain user groups more susceptible?
- Evaluate email authentication controls (SPF, DKIM, DMARC) across all sending domains
