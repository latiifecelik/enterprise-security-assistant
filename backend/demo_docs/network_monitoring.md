# Network Monitoring and Threat Detection Guide

## Overview

This guide covers network-level monitoring for SOC analysts. It describes
key log sources, indicators of compromise at the network level, and
investigation procedures for suspicious network activity.

---

## 1. Network Indicators of Compromise (IOCs)

### Connection Patterns

Suspicious network patterns that warrant investigation:

- **Beaconing**: Regular, periodic outbound connections to the same external host,
  especially at fixed intervals (e.g., every 60 seconds). Beaconing is a hallmark
  of command-and-control (C2) communication.

- **Large outbound data transfers**: Unusual volumes of data leaving the organisation,
  especially to cloud storage, paste sites, or file-sharing services not normally used.

- **Connections to unusual ports**: Outbound connections on non-standard ports
  (e.g., HTTP/HTTPS on ports other than 80/443, SSH on non-standard ports).

- **Connections to newly registered domains**: Threat actors frequently use newly
  registered domains (< 30 days old) for C2 infrastructure.

- **Connections to known-bad IPs/domains**: Matches against threat intelligence feeds,
  blocklists, or known malware infrastructure.

- **Lateral movement indicators**: Internal hosts connecting to other internal hosts
  in unusual ways (e.g., workstations initiating connections to servers on admin ports).

---

## 2. DNS Log Analysis

### Why DNS Logs Matter

DNS is used by virtually every network communication. Malware uses DNS for:
- C2 server resolution
- Data exfiltration via DNS tunnelling
- Domain generation algorithm (DGA) communication
- Fast-flux infrastructure

### Key DNS Indicators

**DNS Tunnelling Signs:**
- Unusually long DNS query strings (>50 characters)
- High volume of DNS queries to a single domain
- DNS record types rarely used in legitimate traffic (TXT, NULL, CNAME queries with long payloads)
- Queries to domains with high entropy names (e.g., `a1b2c3d4e5f6.evil.com`)

**DGA Indicators:**
- Queries to many non-existent domains (NXDOMAIN responses)
- Domain names that appear algorithmically generated (random character sequences)
- Consistent pattern across multiple endpoints

**Investigation Steps for Suspicious DNS:**
1. Identify all queries from the affected host over the time window
2. Check the query volume — how many queries per minute?
3. Analyse the domain names — are they human-readable or random?
4. Check when the domain was registered (WHOIS / passive DNS)
5. Look up the domain in threat intelligence platforms
6. Determine if any queries returned valid responses and if connections followed

---

## 3. Firewall Log Analysis

### What Firewalls Record

Firewall logs capture network flows: source IP, destination IP, source port,
destination port, protocol, bytes transferred, and action (allow/deny).

### Key Analysis Techniques

**Identify Top Talkers:**
- Which internal hosts are generating the most outbound traffic?
- Are any internal hosts receiving unusual amounts of inbound traffic?

**Unusual Outbound Destinations:**
- Connections to countries the organisation does not normally interact with
- Connections to IP ranges associated with cloud providers not used by the organisation
- Connections to Tor exit nodes or anonymisation services

**Denied Traffic Patterns:**
- Bursts of denied outbound connections may indicate malware trying to reach C2
- Denied connections attempting to reach internal hosts may indicate lateral movement

**Port Analysis:**
- Outbound connections on TCP 4444, 5555, 8080, 8888 — common reverse shell ports
- Outbound connections on TCP 22 (SSH) from hosts that should not be running SSH
- Connections on non-standard ports to known HTTP/S destinations

---

## 4. Proxy Log Analysis

### What Proxy Logs Contain

Proxy logs record web requests made by internal hosts, including:
- Source IP and username (if authenticated proxy)
- Full URL requested
- HTTP method and response code
- Response size and content type
- User-agent string

### Suspicious Proxy Patterns

**C2 Communication:**
- Regular requests to the same URL at consistent intervals
- Small requests with small responses (likely C2 check-ins)
- Requests to IP addresses rather than domain names
- Requests with suspicious or empty user-agent strings

**Data Exfiltration:**
- Large POST or PUT requests to external sites (data being uploaded)
- Requests to file-sharing, paste, or cloud storage services not authorised
- Encrypted uploads (HTTPS) with large payloads to unknown destinations

**Malware Indicators:**
- Requests to known malware distribution sites
- Downloads of executables (.exe, .dll, .ps1, .bat) from external sources
- Requests matching known malware user-agent strings

---

## 5. Investigating Suspicious Network Connections

### When to Investigate

Investigate network connections when:
- A host is connecting to a known malicious IP or domain
- An endpoint is sending unusually large amounts of data outbound
- A connection pattern matches beaconing behaviour
- A host is attempting to connect to multiple internal hosts (lateral movement)
- A connection is made to an unusual port on a legitimate service

### Investigation Workflow

1. **Identify the source host**
   - Get the hostname and IP address
   - Determine which user was logged on at the time
   - Review the host's security posture (patched? AV installed?)

2. **Analyse the destination**
   - Resolve the destination IP to a hostname
   - Check the destination against threat intelligence feeds
   - Determine if the destination is a known legitimate service
   - Review WHOIS information for the destination domain

3. **Review connection details**
   - Volume of data transferred (bytes in / bytes out)
   - Duration of the connection
   - Protocol and port
   - Number of connections to the same destination

4. **Correlate with endpoint activity**
   - What process initiated the connection? (EDR telemetry)
   - Is the process legitimate? Is it signed?
   - Are there associated file system or registry changes?

5. **Expand the scope**
   - Are other hosts connecting to the same destination?
   - Is this a known pattern (e.g., software update service)?
   - Does the connection correlate with other alerts?

---

## 6. Network Log Retention and Collection

### Recommended Retention Periods

| Log Type | Recommended Retention |
|---------|----------------------|
| Firewall flows | 90 days |
| Proxy logs | 90 days |
| DNS query logs | 30 days |
| Full packet captures | 7 days (storage-intensive) |
| NetFlow/IPFIX | 30 days |

### Critical Collection Points

1. **Perimeter**: Ingress/egress firewall
2. **Segmentation**: Internal firewalls between zones
3. **DNS**: Recursive resolvers used by internal hosts
4. **Proxy**: Forward proxy for web traffic
5. **VPN gateway**: Remote access authentication and traffic
6. **Active Directory**: Domain controller network activity
