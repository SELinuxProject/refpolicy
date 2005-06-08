#
# network_interface(linux_interfacename,mls_sensitivity)
#
define(`network_interface',`
requires_block_template(`type unlabeled_t')
type $1_netif_t alias netif_$1_t, netif_type;
netifcon $1 context_template(system_u:object_r:$1_netif_t,$2) context_template(system_u:object_r:unlabeled_t,$2)
')

#
# network_node(node_name,mls_sensitivity,address,netmask)
#
define(`network_node',`
type $1_node_t alias node_$1_t, node_type;
nodecon $3 $4 context_template(system_u:object_r:$1_node_t,$2)
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
ifelse(eval($3 < 1024),1,`typeattribute $1 reserved_port_type;',`dnl')
portcon $2 $3 context_template(system_u:object_r:$1,$4)
ifelse(`$5',`',`',`declare_ports($1,shiftn(4,$*))')dnl
')

#
# network_port(port_name,protocol portnum mls_sensitivity [,protocol portnum mls_sensitivity[,...]])
#
define(`network_port',`
type $1_port_t, port_type;
declare_ports($1_port_t,shift($*))
')
