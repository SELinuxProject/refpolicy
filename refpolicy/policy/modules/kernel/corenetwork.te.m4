#
# shiftn(num,list...)
#
# shift the list num times
#
define(`shiftn',`ifelse($1,0,`shift($*)',`shiftn(decr($1),shift(shift($*)))')')

define(`declare_netifs',`dnl
netifcon $2 gen_context(system_u:object_r:$1,$3) gen_context(system_u:object_r:unlabeled_t,$3)
ifelse(`$4',`',`',`declare_netifs($1,shiftn(3,$*))')dnl
')

#
# network_interface(if_name,linux_interface,mls_sensitivity)
#
define(`network_interface',`
gen_require(`type unlabeled_t')
type $1_netif_t alias netif_$1_t, netif_type;
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
type $1_node_t alias node_$1_t, node_type;
declare_nodes($1_node_t,shift($*))
')

# These next three macros have formatting, and should not me indented
define(`determine_reserved_capability',`dnl
ifelse(eval($2 < 1024),1,``allow' dollarsone self:capability net_bind_service;',`dnl
ifelse($4,`',`',`determine_reserved_capability(shiftn(3,$*))')dnl end inner ifelse
')dnl end outer ifelse
') dnl end determine reserved capability

define(`determine_reserved_capability_depend',`dnl
ifelse(eval($2 < 1024),1,`class capability net_bind_service;',`dnl
ifelse($4,`',`',`determine_reserved_capability_depend(shiftn(3,$*))')dnl end inner ifelse
')dnl end outer ifelse
') dnl end determine reserved capability depend

define(`declare_ports',`dnl
ifelse(eval($3 < 1024),1,`
typeattribute $1 reserved_port_type;
#bindresvport in glibc starts searching for reserved ports at 600
ifelse(eval($3 >= 600),1,`typeattribute $1 rpc_port_type;',`dnl')
',`dnl')
portcon $2 $3 gen_context(system_u:object_r:$1,$4)
ifelse(`$5',`',`',`declare_ports($1,shiftn(4,$*))')dnl
')

#
# network_port(port_name,protocol portnum mls_sensitivity [,protocol portnum mls_sensitivity[,...]])
#
define(`network_port',`
type $1_port_t, port_type;
declare_ports($1_port_t,shift($*))
')
