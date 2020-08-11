#
# shiftn(num,list...)
#
# shift the list num times
#
define(`shiftn',`ifelse($1,0,`shift($*)',`shiftn(decr($1),shift(shift($*)))')')

#
# range_start(num)
#
# return the low port in a range.
#
# range_start(600) returns "600"
# range_start(1200-1600) returns "1200"
#
define(`range_start',`ifelse(-1,index(`$1', `-'),$1,substr($1,0,index(`$1', `-')))')

#
# build_option(option_name,true,[false])
#
# makes an ifdef.  hacky quoting changes because with
# regular quoting, the macros in $2 and $3 will not be expanded
#
define(`build_option',`dnl
changequote([,])dnl
[ifdef(`$1',`]
changequote(`,')dnl
$2
changequote([,])dnl
[',`]
changequote(`,')dnl
$3
changequote([,])dnl
[')]
changequote(`,')dnl
')

define(`declare_netifs',`dnl
netifcon $2 gen_context(system_u:object_r:$1,$3) gen_context(system_u:object_r:unlabeled_t,$3)
ifelse(`$4',`',`',`declare_netifs($1,shiftn(3,$*))')dnl
')

#
# network_interface(if_name,linux_interface,mls_sensitivity)
#
define(`network_interface',`
gen_require(``type unlabeled_t;'')  #selint-disable:S-001
type $1_netif_t, netif_type;
declare_netifs($1_netif_t,shift($*))
')

define(`network_interface_controlled',`
ifdef(`__network_enabled_declared__',`',`
## <desc>
## <p>
## Enable network traffic on all controlled interfaces.
## </p>
## </desc>
gen_bool(network_enabled, true)
define(`__network_enabled_declared__')
')
gen_require(``type unlabeled_t;'')  #selint-disable:S-001
type $1_netif_t, netif_type;
declare_netifs($1_netif_t,shift($*))
')

define(`declare_nodes',`dnl
nodecon $3 $4 gen_context(system_u:object_r:$1,$2)
ifelse(`$5',`',`',`declare_nodes($1,shiftn(4,$*))')dnl
')

#
# network_node(node_name,mls_sensitivity,address,netmask[, mls_sensitivity,address,netmask, [...]])
#
define(`network_node',`
type $1_node_t, node_type;
declare_nodes($1_node_t,shift($*))
')

define(`declare_portcons',`dnl
portcon $2 $3 gen_context(system_u:object_r:$1,$4)
ifelse(`$5',`',`',`declare_portcons($1,shiftn(4,$*))')dnl
')

define(`add_port_attribute',`dnl
ifelse(eval(range_start($2) < 1024),1,`typeattribute $1 reserved_port_type;',`typeattribute $1 unreserved_port_type;')
')

# bindresvport in glibc starts searching for reserved ports at 512
define(`add_rpc_attribute',`dnl
ifelse(eval(range_start($3) >= 512 && range_start($3) < 1024),1,`typeattribute $1 rpc_port_type;
',`ifelse(`$5',`',`',`add_rpc_attribute($1,shiftn(4,$*))')')dnl
')

#
# network_port(port_name,protocol portnum mls_sensitivity [,protocol portnum mls_sensitivity[,...]])
#
define(`network_port',`
type $1_port_t, port_type, defined_port_type;
type $1_client_packet_t, packet_type, client_packet_type;
type $1_server_packet_t, packet_type, server_packet_type;
ifelse(`$2',`',`',`add_port_attribute($1_port_t,$3)')dnl
ifelse(`$2',`',`',`add_rpc_attribute($1_port_t,shift($*))')dnl
ifelse(`$2',`',`',`declare_portcons($1_port_t,shift($*))')dnl
')

#
# network_packet(packet_name)
#
define(`network_packet',`
type $1_client_packet_t, packet_type, client_packet_type;
type $1_server_packet_t, packet_type, server_packet_type;
')

#
# network_packet_simple(packet_name)
#
define(`network_packet_simple',`
type $1_packet_t, packet_type;
')

define(`declare_ibpkeycons',`dnl
ibpkeycon $2 $3 gen_context(system_u:object_r:$1,$4)
ifelse(`$5',`',`',`declare_ibpkeycons($1,shiftn(4,$*))')dnl
')

#
# ib_pkey(nam, subnet_prefix, pkey_num, mls_sensitivity [,subnet_prefix, pkey_num, mls_sensitivity[,...]])
#
define(`ib_pkey',`
type $1_ibpkey_t, ibpkey_type;
ifelse(`$2',`',`',`declare_ibpkeycons($1_ibpkey_t,shift($*))')dnl
')

define(`declare_ibendportcons',`dnl
ibendportcon $2 $3 gen_context(system_u:object_r:$1,$4)
ifelse(`$5',`',`',`declare_ibendportcons($1,shiftn(4,$*))')dnl
')

#
# ib_endport (name, dev_name, port_num, mls_sensitivity [, dev_name, port_num mls_sensitivity[,...]])
#
define(`ib_endport',`
type $1_ibendport_t, ibendport_type;
ifelse(`$2',`',`',`declare_ibendportcons($1_ibendport_t,shift($*))')dnl
')
