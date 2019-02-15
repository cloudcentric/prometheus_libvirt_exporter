from __future__ import print_function
import sys
import argparse
import libvirt
import sched
import time
import os
import socket
from prometheus_client import start_http_server, Gauge
from xml.etree import ElementTree

from keystoneclient.v3 import client as keystoneclient
from keystoneauth1.identity import v3
from keystoneauth1 import session
import novaclient.client
import novaclient.exceptions

parser = argparse.ArgumentParser(description='libvirt_exporter scrapes domains metrics from libvirt daemon')
parser.add_argument('-si','--scrape_interval', help='scrape interval for metrics in seconds', default= 5)
parser.add_argument('-uri','--uniform_resource_identifier', help='Libvirt Uniform Resource Identifier', default= "qemu:///system")
parser.add_argument('-p','--port', help='exporter port', default= "9177")

parser.add_argument("-v", "--verbose", action="count")
parser.add_argument("--no-disable", default=False, action="store_true")
parser.add_argument("--region", default=os.environ.get('OS_REGION_NAME'))
parser.add_argument(
    '--os-interface',
    metavar='<interface>',
    dest='interface',
    choices=['admin', 'public', 'internal'],
    default=os.environ.get('OS_INTERFACE', 'admin'),
    help=('Select an interface type.'
          ' Valid interface types: [admin, public, internal].'
          ' (Env: OS_INTERFACE)'),
)

args_os = parser.parse_args()
auth = v3.Password(user_domain_name=os.environ.get('OS_USER_DOMAIN_NAME'),
                   username=os.environ.get('OS_USERNAME'),
                   password=os.environ.get('OS_PASSWORD'),
                   project_domain_name=os.environ.get('OS_PROJECT_DOMAIN_NAME'),
                   project_name=os.environ.get('OS_PROJECT_NAME'),
                   auth_url=os.environ.get('OS_AUTH_URL'))
keystonesession = session.Session(auth=auth)
keystone = keystoneclient.Client(session=keystonesession, endpoint_type=args_os.interface)
nova = novaclient.client.Client("2", session=keystonesession, endpoint_type=args_os.interface, region_name=args_os.region)


args = vars(parser.parse_args())
uri = args["uniform_resource_identifier"]

tenant_instance_cache = {}
tenant_name_instance_cache = {}

def add_tenant_instance_relation(uuid):

        server = nova.servers.get(uuid)

        tenant_instance_cache[server.id] = server.tenant_id

        print(tenant_instance_cache)

def update_tenant_instance_relation():

    tenant_instance_cache.clear()

    hostname = socket.gethostbyaddr(socket.gethostname())[0]
    server = nova.servers.list(search_opts={"all_tenants": 1, "host": hostname})

    for srv in server:
        tenant_instance_cache[srv.id] = srv.tenant_id

    print(tenant_instance_cache)

def add_tenant_name_instance_relation(uuid):

        server = nova.servers.get(uuid)

        project = keystone.projects.get(server.tenant_id)
        tenant_name_instance_cache[server.id] = project.name

        print(tenant_name_instance_cache)

def update_tenant_name_instance_relation():

    tenant_name_instance_cache.clear()

    hostname = socket.gethostbyaddr(socket.gethostname())[0]
    server = nova.servers.list(search_opts={"all_tenants": 1, "host": hostname})

    for srv in server:
         project = keystone.projects.get(srv.tenant_id)
         tenant_name_instance_cache[srv.id] = project.name

    print(tenant_name_instance_cache)

def get_tenant(uuid):

    max_retries = 3
    for i in range(max_retries):
      try:
        tenant_id = tenant_instance_cache[uuid]
        return tenant_id
      except KeyError as e:
        add_tenant_instance_relation(uuid)
        continue
    return None

def get_tenant_name(uuid):

    max_retries = 3
    for i in range(max_retries):
      try:
        tenant_name = tenant_name_instance_cache[uuid]
        return tenant_name
      except KeyError as e:
        add_tenant_name_instance_relation(uuid)
        continue
    return None

def connect_to_uri(uri):
    conn = libvirt.open(uri)

    if conn == None:
        print('Failed to open connection to ' + uri, file = sys.stderr)
    else:
        print('Successfully connected to ' + uri)
    return conn


def get_domains(conn):

    domains = []

    for id in conn.listDomainsID():
        dom = conn.lookupByID(id)

        if dom == None:
            print('Failed to find the domain ' + dom.name(), file=sys.stderr)
        else:
            domains.append(dom)

    if len(domains) == 0:
        print('No running domains in URI')
        return None
    else:
        return domains


def get_metrics_collections(dom, metric_names, labels, stats):
    dimensions = []
    metrics_collection = {}

    labels['uuid'] = dom.UUIDString()
    labels['project_id'] = get_tenant(dom.UUIDString())
    labels['project_name'] = get_tenant_name(dom.UUIDString())

    for mn in metric_names:
        if type(stats) is list:
            dimensions = [[stats[0][mn], labels]]
        elif type(stats) is dict:
            dimensions = [[stats[mn], labels]]
        metrics_collection[mn] = dimensions

    return metrics_collection


def get_metrics_multidim_collections(dom, metric_names, device):

    tree = ElementTree.fromstring(dom.XMLDesc())
    targets = []

    for target in tree.findall("devices/" + device + "/target"): # !
        targets.append(target.get("dev"))

    metrics_collection = {}

    for mn in metric_names:
        dimensions = []
        for target in targets:
            labels = {'domain': dom.name()}
            labels['target_device'] = target
            labels['uuid'] = dom.UUIDString()
            labels['project_id'] = get_tenant(dom.UUIDString())
            labels['project_name'] = get_tenant_name(dom.UUIDString())
            if device == "interface":
                stats = dom.interfaceStats(target) # !
            elif device == "disk":
                stats = list(dom.blockStats(target))
                stats_flags = dom.blockStatsFlags(target, 0)
                stats.append(stats_flags['wr_total_times'])
                stats.append(stats_flags['rd_total_times'])
                stats.append(stats_flags['flush_total_times'])
                stats.append(stats_flags['flush_operations'])
            stats = dict(zip(metric_names, stats))
            dimension = [stats[mn], labels]
            dimensions.append(dimension)
            labels = None
        metrics_collection[mn] = dimensions

    return metrics_collection


def add_metrics(dom, header_mn, g_dict, dom_list):

    labels = {'domain':dom.name()}

    if header_mn == "libvirt_cpu_stats_":

        stats = dom.getCPUStats(True)
        metric_names = stats[0].keys()
        metrics_collection = get_metrics_collections(dom, metric_names, labels, stats)
        unit = "_nanosecs"

    elif header_mn == "libvirt_mem_stats_":
        stats = dom.memoryStats()
        metric_names = stats.keys()
        metrics_collection = get_metrics_collections(dom, metric_names, labels, stats)
        unit = ""

    elif header_mn == "libvirt_block_stats_":

        metric_names = \
        ['read_requests_issued',
        'read_bytes' ,
        'write_requests_issued',
        'write_bytes',
        'errors_number',
        'writes_total_time',
        'reads_total_time',
        'flush_total_times',
        'flush_operations']

        metrics_collection = get_metrics_multidim_collections(dom, metric_names, device="disk")
        unit = ""

    elif header_mn == "libvirt_interface_":

        metric_names = \
        ['read_bytes',
        'read_packets',
        'read_errors',
        'read_drops',
        'write_bytes',
        'write_packets',
        'write_errors',
        'write_drops']

        metrics_collection = get_metrics_multidim_collections(dom, metric_names, device="interface")
        unit = ""

    for mn in metrics_collection:
        metric_name = header_mn + mn + unit
        dimensions = metrics_collection[mn]

        if metric_name not in g_dict.keys():

            metric_help = 'help'
            labels_names = metrics_collection[mn][0][1].keys()
            g_dict[metric_name] = Gauge(metric_name, metric_help, labels_names)

            for dimension in dimensions:
                dimension_metric_value = dimension[0]
                dimension_label_values = dimension[1].values()
                g_dict[metric_name].labels(*dimension_label_values).set(dimension_metric_value)
                dom_list[dom.name()][metric_name] = dimension_label_values
        else:
            for dimension in dimensions:
                dimension_metric_value = dimension[0]
                dimension_label_values = dimension[1].values()
                g_dict[metric_name].labels(*dimension_label_values).set(dimension_metric_value)
                dom_list[dom.name()][metric_name] = dimension_label_values
    return g_dict


def job(dom_list, uri, g_dict, scheduler):
    print('BEGIN JOB :', time.time())
    conn = connect_to_uri(uri)
    domains = get_domains(conn)
    while domains is None:
        domains = get_domains(conn)
        time.sleep(int(args["scrape_interval"]))

    for dom in domains:
        if dom.name() in dom_list.keys():
            dom_list[dom.name()].clear()

    for key, value in dom_list.iteritems():
        for d_key, d_value in value.iteritems():
            g_dict[d_key].remove(*d_value)

    dom_list.clear()

    headers_mn = ["libvirt_cpu_stats_", "libvirt_mem_stats_", \
                  "libvirt_block_stats_", "libvirt_interface_"]

    for dom in domains:

        if dom.isActive():
            print(dom.name())
            dom_list[dom.name()] = {}

            for header_mn in headers_mn:
                try:
                    g_dict = add_metrics(dom, header_mn, g_dict, dom_list)
                except:
                    pass


    conn.close()
    print('FINISH JOB :', time.time())
    scheduler.enter((int(args["scrape_interval"])), 1, job, (dom_list, uri, g_dict, scheduler))

def update_tenant(scheduler):
    print('Start updating tenant information', time.time())
    update_tenant_instance_relation()
    update_tenant_name_instance_relation()
    scheduler.enter(int(args["scrape_interval"])*3600, 2, update_tenant, (scheduler,))

def main():

    start_http_server(int(args_os.port))

    g_dict = {}
    dom_list = {}

    scheduler = sched.scheduler(time.time, time.sleep)
    print('START:', time.time())
    update_tenant(scheduler)
    job(dom_list, uri, g_dict, scheduler)
    scheduler.run()

if __name__ == '__main__':
    main()
