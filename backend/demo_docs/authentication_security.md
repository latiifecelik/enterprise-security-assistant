# Authentication Security Guide

## Overview

This guide provides SOC analysts with reference material for investigating
authentication-related security events. It covers common attack patterns,
detection strategies, and recommended investigation procedures.

---

## 1. Failed Login Analysis

### What to Look For

When reviewing failed authentication events, analysts should consider:

- **Frequency**: How many failures in what time window?
- **Source diversity**: Are failures from one IP or many?
- **Target diversity**: Are failures targeting one account or many?
- **Timing pattern**: Random intervals (human) or regular intervals (tool)?
- **Credential pattern**: Same username variations? Known username list?
- **Protocol**: SSH, RDP, web application, VPN, API?

### Key Thresholds (Adjust to Your Environment)

| Pattern | Threshold | Likely Attack Type |
|---------|-----------|-------------------|
| Same IP, same account | >10 failures in 5 minutes | Brute Force |
| Same IP, many accounts | >5 accounts in 10 minutes | Password Spraying |
| Many IPs, same account | >20 failures, distributed | Credential Stuffing |
| Low and slow failures | <3 per hour, sustained | Low-and-Slow Brute Force |

---

## 2. Brute Force Attacks

### Definition

A brute-force attack systematically attempts a large number of password combinations
against a single account or service until one succeeds. The attacker uses automated
tools to submit credentials at high speed.

### Characteristics

- **High volume**: Hundreds or thousands of attempts in a short period
- **Single target**: Usually one username or a small set of usernames
- **Sequential patterns**: Attempts may follow dictionary wordlists
- **Source**: Often a single IP address (unless the attacker uses proxies)
- **Tool signatures**: Consistent user-agent strings, regular timing intervals

### Detection Indicators

- Event ID 4625 (Windows) spike for a specific account
- SSH failure entries in `/var/log/auth.log` from one source IP
- Web application returning HTTP 401 at high rate
- Account lockout events (Event ID 4740) for the same account

### Investigation Steps

1. Identify the targeted account and source IP
2. Determine whether a lockout policy is in place
3. Check whether any attempt succeeded (Event ID 4624 / successful SSH connection)
4. Review whether the source IP is a known threat actor
5. Correlate with other activity from the same source

---

## 3. Password Spraying

### Definition

Password spraying is an attack where an adversary attempts a small number of commonly
used passwords against a large number of accounts. Unlike brute force, which targets
one account intensively, password spraying targets many accounts with few attempts
each, often evading per-account lockout policies.

### Why Password Spraying is Dangerous

- **Evades lockout policies**: Only 1-3 attempts per account means most lockout
  thresholds are never triggered.
- **Hard to detect with per-account rules**: Individual account activity looks normal.
- **Effective against weak passwords**: Commonly used passwords (e.g., `Company2024!`,
  `Welcome1`, `Password123`) appear in many accounts.
- **Scales easily**: Automated tools can spray thousands of accounts in minutes.

### Characteristics

- **Low volume per account**: Typically 1-3 attempts per username
- **High breadth**: Targets many usernames (sometimes entire directory)
- **Common passwords used**: Seasonal passwords, organisation name, default passwords
- **Distributed timing**: Attempts may be spaced to avoid rate limiting

### Detection Indicators

- Many unique accounts showing 1-3 failed logins in a short window
- Same source IP or subnet attempting multiple accounts
- Failures occurring during unusual hours (e.g., 3 AM for a domestic organisation)
- Attempts against accounts that are rarely used or service accounts

### Investigation Steps

1. Identify all accounts targeted from the suspicious source
2. Determine the password(s) used in the attempts
3. Check whether any account had a successful login after the spray
4. Correlate timing with threat intelligence (known spray campaigns)
5. Review whether MFA is enforced — spray attacks are blocked by MFA

---

## 4. Credential Stuffing

### Definition

Credential stuffing uses large lists of username/password combinations obtained from
previous data breaches. Unlike brute force, the credentials are real (leaked from other
services), and attackers rely on users reusing passwords across multiple services.

### Characteristics

- **Real credentials**: Attacker uses known valid credential pairs
- **High success rate**: Typically 0.1%-2% of leaked credentials succeed
- **Large scale**: Attacks may test millions of credential pairs
- **Distributed sources**: Often uses residential proxy networks or botnets
- **Known breach correlation**: Credentials match data from haveibeenpwned.com or dark web

### Detection Indicators

- High volume of login attempts with varied usernames (not sequential)
- Attempts using diverse IP addresses (residential proxies)
- User-agent strings matching known stuffing tools (Sentry MBA, Bullet Ogre, etc.)
- Successful logins from users who have never logged in from a particular geography
- User reports of account access they did not initiate

### Investigation Steps

1. Obtain sample credential pairs from the attack traffic
2. Cross-reference usernames against recent public breach data
3. Check whether successful accounts share credentials with breached services
4. Review what actions were taken during any successful stuffing sessions
5. Notify affected users to change passwords and enable MFA

---

## 5. Suspicious Successful Login Investigation

### When a Login Should Be Investigated

A successful login requires investigation when it follows anomalous patterns:

- Preceded by multiple failed login attempts from the same source
- Originates from an unusual geographic location for that user
- Occurs at an unusual time (e.g., 3 AM for an employee in one timezone)
- Uses an unfamiliar device or operating system
- Is the first login from that IP address or ASN
- User has not been active recently

### Key Questions

1. **Is the source IP legitimate?**
   - Check against known corporate VPN ranges
   - Check against known threat intelligence feeds
   - Geolocate the IP — is the location plausible for this user?

2. **Is the timing plausible?**
   - Does the login time match the user's normal working hours?
   - Could the user have travelled to explain a location change?

3. **What did the session do?**
   - Were sensitive files accessed?
   - Were settings changed (email forwarding, MFA devices, recovery email)?
   - Were any downloads or exports performed?
   - Were administrative actions taken?

4. **Can the user confirm the activity?**
   - Contact the user through an out-of-band channel (phone, not email)
   - If the user denies the activity, treat as confirmed compromise

---

## 6. Recommended Log Sources for Authentication Investigation

### Windows Environments

| Log Source | Key Event IDs | Description |
|-----------|--------------|-------------|
| Windows Security Log | 4624, 4625, 4634, 4647 | Logon/logoff events |
| Windows Security Log | 4648, 4672, 4768, 4769 | Special/Kerberos logon |
| Windows Security Log | 4740, 4767 | Account lockout/unlock |
| Active Directory | 4771, 4776 | Kerberos pre-auth, NTLM |
| PowerShell Logs | 4103, 4104 | Script execution |

### Linux/Unix Environments

| Log Source | Location | Description |
|-----------|----------|-------------|
| Authentication log | `/var/log/auth.log` | All auth events (Debian/Ubuntu) |
| Secure log | `/var/log/secure` | Auth events (RHEL/CentOS) |
| SSH daemon log | `/var/log/sshd.log` | Detailed SSH events |
| Syslog | `/var/log/syslog` | System events |
| Audit log | `/var/log/audit/audit.log` | Kernel audit events |

### Cloud Platforms

| Platform | Log Source | Key Events |
|---------|-----------|-----------|
| Microsoft 365 | Azure AD Sign-in Logs | Interactive and non-interactive logins |
| Microsoft 365 | Unified Audit Log | All M365 activity |
| AWS | CloudTrail | Console/API authentication |
| GCP | Cloud Audit Logs | Authentication and authorisation |

### Network-Level

- **VPN gateway logs**: Authentication success/failure, session duration, data volume
- **Firewall logs**: Source/destination correlation for authenticated sessions
- **Proxy logs**: Web activity following authentication
- **DNS logs**: Domain lookups made during authenticated sessions
