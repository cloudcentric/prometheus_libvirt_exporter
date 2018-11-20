# Prometheus libvirt exporter

Prometheus libvirt exporter is tool for scraping metrics from libvirt daemon and exposing those metric in prometheus format.
This exporter connects to any libvirt daemon and exports per-domain metrics related to CPU, memory, disk and network usage.
Metrics are exposing on port 9177

List of metrics/labels are being exported:
```
libvirt_cpu_stats_system_time_nanosecs{domain=""}
libvirt_cpu_stats_user_time_nanosecs{domain=""}
libvirt_cpu_stats_cpu_time_nanosecs{domain=""}

libvirt_mem_stats_rss{domain=""}
libvirt_mem_stats_swap_in{domain=""}
libvirt_mem_stats_unused{domain=""}
libvirt_mem_stats_minor_fault{domain=""}
libvirt_mem_stats_last_update{domain=""}
libvirt_mem_stats_actual{domain=""}
libvirt_mem_stats_major_fault{domain=""}
libvirt_mem_stats_available{domain=""}

libvirt_block_stats_errors_number{domain="",target_device=""}
libvirt_block_stats_write_requests_issued{domain="",target_device=""}
libvirt_block_stats_write_bytes{domain="",target_device=""}
libvirt_block_stats_read_bytes{domain="",target_device=""}
libvirt_block_stats_read_requests_issued{domain="",target_device=""}

libvirt_interface_write_errors{domain="",target_device=""}
libvirt_interface_write_bytes{domain="",target_device=""}
libvirt_interface_write_packets{domain="",target_device=""}
libvirt_interface_write_drops{domain="-",target_device=""}

libvirt_interface_read_packets{domain="",target_device=""}
libvirt_interface_read_errors{domain="",target_device=""}
libvirt_interface_read_drops{domain="",target_device=""}
libvirt_interface_read_bytes{domain="-",target_device=""}

```

## Getting Started

These instructions will get you a copy of exporter and running on your local machine.

### Prerequisites

What things you need to install in case  

if you want to run exporter on host itself
```
python
libvirt-python==3.7.0
prometheus-client==0.0.21
python-novaclient==7.1.0
python-keystoneclient==3.10.0
```
### Installing

if you want to run exporter on host itself
```
git clone https://github.com/syseleven/prometheus_libvirt_exporter.git
pip install -r requirements.txt
```
### Running
if you want to run exporter on host itself
```
source source.rc

python libvirt_exporter.py -h
usage: libvirt_exporter.py [-h] [-si SCRAPE_INTERVAL]
                           [-uri UNIFORM_RESOURCE_IDENTIFIER] [-v]
                           [--no-disable] [--region REGION]
                           [--os-interface <interface>] [--insecure]
                           [--os-cacert <ca-certificate>]
                           [--os-cert <certificate>] [--os-key <key>]
                           [--timeout <seconds>] [--os-auth-plugin <name>]
                           [--os-auth-url OS_AUTH_URL]
                           [--os-domain-id OS_DOMAIN_ID]
                           [--os-domain-name OS_DOMAIN_NAME]
                           [--os-tenant-id OS_TENANT_ID]
                           [--os-tenant-name OS_TENANT_NAME]
                           [--os-project-id OS_PROJECT_ID]
                           [--os-project-name OS_PROJECT_NAME]
                           [--os-project-domain-id OS_PROJECT_DOMAIN_ID]
                           [--os-project-domain-name OS_PROJECT_DOMAIN_NAME]
                           [--os-trust-id OS_TRUST_ID]
                           [--os-user-id OS_USER_ID]
                           [--os-username OS_USERNAME]
                           [--os-user-domain-id OS_USER_DOMAIN_ID]
                           [--os-user-domain-name OS_USER_DOMAIN_NAME]
                           [--os-password OS_PASSWORD]

libvirt_exporter scrapes domains metrics from libvirt daemon

optional arguments:
  -h, --help            show this help message and exit
  -si SCRAPE_INTERVAL, --scrape_interval SCRAPE_INTERVAL
                        scrape interval for metrics in seconds
  -uri UNIFORM_RESOURCE_IDENTIFIER, --uniform_resource_identifier UNIFORM_RESOURCE_IDENTIFIER
                        Libvirt Uniform Resource Identifier
  -v, --verbose
  --no-disable
  --region REGION
  --os-interface <interface>
                        Select an interface type. Valid interface types:
                        [admin, public, internal]. (Env: OS_INTERFACE)
  --insecure            Explicitly allow client to perform "insecure" TLS
                        (https) requests. The server's certificate will not be
                        verified against any certificate authorities. This
                        option should be used with caution.
  --os-cacert <ca-certificate>
                        Specify a CA bundle file to use in verifying a TLS
                        (https) server certificate. Defaults to
                        env[OS_CACERT].
  --os-cert <certificate>
                        Defaults to env[OS_CERT].
  --os-key <key>        Defaults to env[OS_KEY].
  --timeout <seconds>   Set request timeout (in seconds).
  --os-auth-plugin <name>
                        The auth plugin to load

Authentication Options:
  Options specific to the password plugin.

  --os-auth-url OS_AUTH_URL
                        Authentication URL
  --os-domain-id OS_DOMAIN_ID
                        Domain ID to scope to
  --os-domain-name OS_DOMAIN_NAME
                        Domain name to scope to
  --os-tenant-id OS_TENANT_ID
                        Tenant ID to scope to
  --os-tenant-name OS_TENANT_NAME
                        Tenant name to scope to
  --os-project-id OS_PROJECT_ID
                        Project ID to scope to
  --os-project-name OS_PROJECT_NAME
                        Project name to scope to
  --os-project-domain-id OS_PROJECT_DOMAIN_ID
                        Domain ID containing project
  --os-project-domain-name OS_PROJECT_DOMAIN_NAME
                        Domain name containing project
  --os-trust-id OS_TRUST_ID
                        Trust ID
  --os-user-id OS_USER_ID
                        User id
  --os-username OS_USERNAME, --os-user_name OS_USERNAME
                        Username
  --os-user-domain-id OS_USER_DOMAIN_ID
                        User's domain id
  --os-user-domain-name OS_USER_DOMAIN_NAME
                        User's domain name
  --os-password OS_PASSWORD
                        User's password
```
