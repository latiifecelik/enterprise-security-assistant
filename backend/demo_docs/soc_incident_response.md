# SOC Incident Response Playbook

## Purpose

This playbook provides structured guidance for Security Operations Centre (SOC) analysts
responding to security incidents. It establishes a consistent, repeatable process for
detecting, analysing, containing, and recovering from cybersecurity events.

---

## 1. Incident Classification

### Severity Levels

**Critical (P1)** — Immediate response required
- Active data exfiltration
- Ransomware execution
- Confirmed account compromise with privileged access
- Compromise of critical infrastructure systems

**High (P2)** — Response within 1 hour
- Suspected credential compromise
- Successful authentication from unusual geography or device
- Multiple failed logins followed by successful login from same source
- Malware detected on endpoint

**Medium (P3)** — Response within 4 hours
- Repeated failed authentication attempts (brute force indicators)
- Unusual user behaviour patterns
- Suspicious outbound connection detected

**Low (P4)** — Response within 24 hours
- Isolated policy violations
- Single failed login from known user
- Informational alerts requiring review

---

## 2. Initial Triage

When an alert is received, the analyst must:

1. **Verify the alert is not a false positive**
   - Check alert confidence score
   - Review raw log data behind the alert
   - Compare with baseline user behaviour

2. **Identify the affected assets**
   - Which user accounts are involved?
   - Which systems or hosts are affected?
   - What data or services are at risk?

3. **Determine incident scope**
   - Is this isolated to one user or system?
   - Is there lateral movement evidence?
   - Are multiple accounts showing similar behaviour?

4. **Assign severity**
   - Use the classification table above
   - Document reasoning for severity assignment

---

## 3. Evidence Collection

Evidence must be collected promptly before systems are modified or logs rotate.

### Authentication Events

Collect the following for authentication-related incidents:

- **Windows Security Event Logs**
  - Event ID 4625: Failed logon
  - Event ID 4624: Successful logon
  - Event ID 4648: Logon using explicit credentials
  - Event ID 4776: Credential validation attempt

- **Linux/Unix Authentication Logs**
  - `/var/log/auth.log` or `/var/log/secure`
  - SSH daemon logs (`/var/log/sshd.log`)
  - PAM (Pluggable Authentication Module) logs

- **VPN and Remote Access Logs**
  - Connection timestamps and durations
  - Source IP addresses and geographic location
  - Device fingerprints or certificates used

- **Cloud Platform Logs**
  - Azure AD / Entra ID sign-in logs
  - AWS CloudTrail authentication events
  - GCP Cloud Audit Logs

### Network Evidence

- Firewall logs (source/destination IPs, ports, protocols)
- DNS query logs for the affected hosts
- Proxy logs showing web activity
- NetFlow or packet captures if available

### Endpoint Evidence

- Running processes at time of incident
- Scheduled tasks and startup items
- Recently modified files and registry keys
- Browser history and downloaded files

---

## 4. Authentication Incidents

### Scenario: Multiple Failed SSH Logins Followed by Successful Login

This pattern is a strong indicator of a brute-force or credential-stuffing attack
that eventually succeeded.

**Investigation steps:**

1. **Identify the source IP**
   - Is the IP known? Check against threat intelligence feeds.
   - Is the IP internal or external?
   - Has this IP appeared in previous incidents?

2. **Review the timeline**
   - How many failed attempts preceded the success?
   - What was the time interval between attempts?
   - Did attempts come from a single IP or multiple IPs (distributed)?

3. **Examine the successful session**
   - What commands were executed after login?
   - Were any files accessed, modified, or exfiltrated?
   - Were new accounts created or privilege escalations attempted?
   - Were any persistence mechanisms installed (cron jobs, SSH keys, services)?

4. **Check for lateral movement**
   - Did the compromised account access other systems?
   - Are there outbound connections to unfamiliar hosts?
   - Were any internal credentials accessed?

5. **Preserve evidence**
   - Capture current running processes: `ps aux`
   - Check active network connections: `netstat -antp` or `ss -antp`
   - Dump bash history: `~/.bash_history`
   - Collect SSH authorised keys: `~/.ssh/authorized_keys`

---

## 5. Containment

Containment should be executed as quickly as possible once scope is understood.

### Immediate Containment Actions

- **Disable compromised accounts** in Active Directory / LDAP / cloud IAM
- **Block source IP addresses** at the firewall or security group level
- **Revoke active sessions** and invalidate tokens
- **Isolate affected hosts** from the network if necessary (last resort)
- **Force password resets** for affected accounts and any accounts that may share credentials

### Preserve Forensic State

Before making changes:
- Take memory snapshots if feasible
- Capture disk images of critical systems
- Export relevant logs to secure storage

---

## 6. Escalation Criteria

Escalate immediately to the Incident Response team when:
- Privileged accounts (admin, service accounts) are compromised
- Evidence of data exfiltration is found
- The attack appears coordinated across multiple accounts
- Critical infrastructure or production systems are affected
- Regulatory requirements mandate escalation (e.g., GDPR breach notification)

---

## 7. Documentation

Every incident must be documented including:
- Alert trigger and initial indicators
- Timeline of analyst actions
- Evidence collected (with timestamps and chain of custody)
- Severity assessment and reasoning
- Containment actions taken
- Escalation decisions
- Lessons learned and recommended improvements
