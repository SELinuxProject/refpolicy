#
# shiftn(num,list...)
#
# shift the list num times
#
define(`shiftn',`ifelse($1,0,`shift($*)',`shiftn(decr($1),shift(shift($*)))')')

########################################
#
# Network Interface generated macros
#
########################################

define(`create_netif_interfaces',``
########################################
## <summary>
##	Send and receive TCP network traffic on the $1 interface.
## </summary>
## <param name="domain">
##	<summary>
##	Domain allowed access.
##	</summary>
## </param>
## <infoflow type="both" weight="10"/>
#
interface(`corenet_tcp_sendrecv_$1_if',`
	gen_require(`
		$3 $1_$2;
	')

	allow dollarsone $1_$2:netif { egress ingress };
')

########################################
## <summary>
##	Send UDP network traffic on the $1 interface.
## </summary>
## <param name="domain">
##	<summary>
##	Domain allowed access.
##	</summary>
## </param>
## <infoflow type="write" weight="10"/>
#
interface(`corenet_udp_send_$1_if',`
	gen_require(`
		$3 $1_$2;
	')

	allow dollarsone $1_$2:netif { egress };
')

########################################
## <summary>
##	Receive UDP network traffic on the $1 interface.
## </summary>
## <param name="domain">
##	<summary>
##	Domain allowed access.
##	</summary>
## </param>
## <infoflow type="read" weight="10"/>
#
interface(`corenet_udp_receive_$1_if',`
	gen_require(`
		$3 $1_$2;
	')

	allow dollarsone $1_$2:netif { ingress };
')

########################################
## <summary>
##	Send and receive UDP network traffic on the $1 interface.
## </summary>
## <param name="domain">
##	<summary>
##	Domain allowed access.
##	</summary>
## </param>
## <infoflow type="both" weight="10"/>
#
interface(`corenet_udp_sendrecv_$1_if',`
	corenet_udp_send_$1_if(dollarsone)
	corenet_udp_receive_$1_if(dollarsone)
')

########################################
## <summary>
##	Send raw IP packets on the $1 interface.
## </summary>
## <param name="domain">
##	<summary>
##	Domain allowed access.
##	</summary>
## </param>
## <infoflow type="write" weight="10"/>
#
interface(`corenet_raw_send_$1_if',`
	gen_require(`
		$3 $1_$2;
	')

	allow dollarsone $1_$2:netif { egress };
')

########################################
## <summary>
##	Receive raw IP packets on the $1 interface.
## </summary>
## <param name="domain">
##	<summary>
##	Domain allowed access.
##	</summary>
## </param>
## <infoflow type="read" weight="10"/>
#
interface(`corenet_raw_receive_$1_if',`
	gen_require(`
		$3 $1_$2;
	')

	allow dollarsone $1_$2:netif { ingress };
')

########################################
## <summary>
##	Send and receive raw IP packets on the $1 interface.
## </summary>
## <param name="domain">
##	<summary>
##	Domain allowed access.
##	</summary>
## </param>
## <infoflow type="both" weight="10"/>
#
interface(`corenet_raw_sendrecv_$1_if',`
	corenet_raw_send_$1_if(dollarsone)
	corenet_raw_receive_$1_if(dollarsone)
')
'') dnl end create_netif_interfaces

# create confined network interfaces controlled by the network_enabled boolean
# do not call this macro for loop back
define(`create_netif_interfaces_controlled',``
########################################
## <summary>
##	Send and receive TCP network traffic on the $1 interface.
## </summary>
## <param name="domain">
##	<summary>
##	Domain allowed access.
##	</summary>
## </param>
## <infoflow type="both" weight="10"/>
#
interface(`corenet_tcp_sendrecv_$1_if',`
	gen_require(`
		$3 $1_$2;
	')

	if (network_enabled) {
		allow dollarsone $1_$2:netif { egress ingress };
	}
')

########################################
## <summary>
##	Send UDP network traffic on the $1 interface.
## </summary>
## <param name="domain">
##	<summary>
##	Domain allowed access.
##	</summary>
## </param>
## <infoflow type="write" weight="10"/>
#
interface(`corenet_udp_send_$1_if',`
	gen_require(`
		$3 $1_$2;
	')

	if (network_enabled) {
		allow dollarsone $1_$2:netif { egress };
	}
')

########################################
## <summary>
##	Receive UDP network traffic on the $1 interface.
## </summary>
## <param name="domain">
##	<summary>
##	Domain allowed access.
##	</summary>
## </param>
## <infoflow type="read" weight="10"/>
#
interface(`corenet_udp_receive_$1_if',`
	gen_require(`
		$3 $1_$2;
	')

	if (network_enabled) {
		allow dollarsone $1_$2:netif { ingress };
	}
')

########################################
## <summary>
##	Send and receive UDP network traffic on the $1 interface.
## </summary>
## <param name="domain">
##	<summary>
##	Domain allowed access.
##	</summary>
## </param>
## <infoflow type="both" weight="10"/>
#
interface(`corenet_udp_sendrecv_$1_if',`
	corenet_udp_send_$1_if(dollarsone)
	corenet_udp_receive_$1_if(dollarsone)
')

########################################
## <summary>
##	Send raw IP packets on the $1 interface.
## </summary>
## <param name="domain">
##	<summary>
##	Domain allowed access.
##	</summary>
## </param>
## <infoflow type="write" weight="10"/>
#
interface(`corenet_raw_send_$1_if',`
	gen_require(`
		$3 $1_$2;
	')

	if (network_enabled) {
		allow dollarsone $1_$2:netif { egress };
	}
')

########################################
## <summary>
##	Receive raw IP packets on the $1 interface.
## </summary>
## <param name="domain">
##	<summary>
##	Domain allowed access.
##	</summary>
## </param>
## <infoflow type="read" weight="10"/>
#
interface(`corenet_raw_receive_$1_if',`
	gen_require(`
		$3 $1_$2;
	')

	if (network_enabled) {
		allow dollarsone $1_$2:netif { ingress };
	}
')

########################################
## <summary>
##	Send and receive raw IP packets on the $1 interface.
## </summary>
## <param name="domain">
##	<summary>
##	Domain allowed access.
##	</summary>
## </param>
## <infoflow type="both" weight="10"/>
#
interface(`corenet_raw_sendrecv_$1_if',`
	corenet_raw_send_$1_if(dollarsone)
	corenet_raw_receive_$1_if(dollarsone)
')
'') dnl end create_netif_interfaces_controlled

########################################
#
# Network node generated macros
#
########################################

define(`create_node_interfaces',``
########################################
## <summary>
##	Send and receive TCP traffic on the $1 node.
## </summary>
## <param name="domain">
##	<summary>
##	Domain allowed access.
##	</summary>
## </param>
## <infoflow type="both" weight="10"/>
#
interface(`corenet_tcp_sendrecv_$1_node',`
	gen_require(`
		$3 $1_$2;
	')

	allow dollarsone $1_$2:node { sendto recvfrom };
')

########################################
## <summary>
##	Send UDP traffic on the $1 node.
## </summary>
## <param name="domain">
##	<summary>
##	Domain allowed access.
##	</summary>
## </param>
## <infoflow type="write" weight="10"/>
#
interface(`corenet_udp_send_$1_node',`
	gen_require(`
		$3 $1_$2;
	')

	allow dollarsone $1_$2:node { sendto };
')

########################################
## <summary>
##	Receive UDP traffic on the $1 node.
## </summary>
## <param name="domain">
##	<summary>
##	Domain allowed access.
##	</summary>
## </param>
## <infoflow type="read" weight="10"/>
#
interface(`corenet_udp_receive_$1_node',`
	gen_require(`
		$3 $1_$2;
	')

	allow dollarsone $1_$2:node { recvfrom };
')

########################################
## <summary>
##	Send and receive UDP traffic on the $1 node.
## </summary>
## <param name="domain">
##	<summary>
##	Domain allowed access.
##	</summary>
## </param>
## <infoflow type="both" weight="10"/>
#
interface(`corenet_udp_sendrecv_$1_node',`
	corenet_udp_send_$1_node(dollarsone)
	corenet_udp_receive_$1_node(dollarsone)
')

########################################
## <summary>
##	Send raw IP packets on the $1 node.
## </summary>
## <param name="domain">
##	<summary>
##	Domain allowed access.
##	</summary>
## </param>
## <infoflow type="write" weight="10"/>
#
interface(`corenet_raw_send_$1_node',`
	gen_require(`
		$3 $1_$2;
	')

	allow dollarsone $1_$2:node { sendto };
')

########################################
## <summary>
##	Receive raw IP packets on the $1 node.
## </summary>
## <param name="domain">
##	<summary>
##	Domain allowed access.
##	</summary>
## </param>
## <infoflow type="write" weight="10"/>
#
interface(`corenet_raw_receive_$1_node',`
	gen_require(`
		$3 $1_$2;
	')

	allow dollarsone $1_$2:node { recvfrom };
')

########################################
## <summary>
##	Send and receive raw IP packets on the $1 node.
## </summary>
## <param name="domain">
##	<summary>
##	Domain allowed access.
##	</summary>
## </param>
## <infoflow type="both" weight="10"/>
#
interface(`corenet_raw_sendrecv_$1_node',`
	corenet_raw_send_$1_node(dollarsone)
	corenet_raw_receive_$1_node(dollarsone)
')

########################################
## <summary>
##	Bind TCP sockets to node $1.
## </summary>
## <param name="domain">
##	<summary>
##	Domain allowed access.
##	</summary>
## </param>
## <infoflow type="none"/>
#
interface(`corenet_tcp_bind_$1_node',`
	gen_require(`
		$3 $1_$2;
	')

	allow dollarsone $1_$2:tcp_socket node_bind;
')

########################################
## <summary>
##	Bind UDP sockets to the $1 node.
## </summary>
## <param name="domain">
##	<summary>
##	Domain allowed access.
##	</summary>
## </param>
## <infoflow type="none"/>
#
interface(`corenet_udp_bind_$1_node',`
	gen_require(`
		$3 $1_$2;
	')

	allow dollarsone $1_$2:udp_socket node_bind;
')
'') dnl end create_node_interfaces

########################################
#
# Network port generated macros
#
########################################

define(`create_port_interfaces',``
########################################
## <summary>
##	Send and receive TCP traffic on the $1 port.
## </summary>
## <param name="domain">
##	<summary>
##	Domain allowed access.
##	</summary>
## </param>
## <infoflow type="both" weight="10"/>
#
interface(`corenet_tcp_sendrecv_$1_port',`
	refpolicywarn(`dollarszero() has been deprecated, please remove.')
')

########################################
## <summary>
##	Send UDP traffic on the $1 port.
## </summary>
## <param name="domain">
##	<summary>
##	Domain allowed access.
##	</summary>
## </param>
## <infoflow type="write" weight="10"/>
#
interface(`corenet_udp_send_$1_port',`
	refpolicywarn(`dollarszero() has been deprecated, please remove.')
')

########################################
## <summary>
##	Do not audit attempts to send UDP traffic on the $1 port.
## </summary>
## <param name="domain">
##	<summary>
##	Domain to not audit.
##	</summary>
## </param>
## <infoflow type="none"/>
#
interface(`corenet_dontaudit_udp_send_$1_port',`
	refpolicywarn(`dollarszero() has been deprecated, please remove.')
')

########################################
## <summary>
##	Receive UDP traffic on the $1 port.
## </summary>
## <param name="domain">
##	<summary>
##	Domain allowed access.
##	</summary>
## </param>
## <infoflow type="read" weight="10"/>
#
interface(`corenet_udp_receive_$1_port',`
	refpolicywarn(`dollarszero() has been deprecated, please remove.')
')

########################################
## <summary>
##	Do not audit attempts to receive UDP traffic on the $1 port.
## </summary>
## <param name="domain">
##	<summary>
##	Domain to not audit.
##	</summary>
## </param>
## <infoflow type="none"/>
#
interface(`corenet_dontaudit_udp_receive_$1_port',`
	refpolicywarn(`dollarszero() has been deprecated, please remove.')
')

########################################
## <summary>
##	Send and receive UDP traffic on the $1 port.
## </summary>
## <param name="domain">
##	<summary>
##	Domain allowed access.
##	</summary>
## </param>
## <infoflow type="both" weight="10"/>
#
interface(`corenet_udp_sendrecv_$1_port',`
	refpolicywarn(`dollarszero() has been deprecated, please remove.')
')

########################################
## <summary>
##	Do not audit attempts to send and receive
##	UDP traffic on the $1 port.
## </summary>
## <param name="domain">
##	<summary>
##	Domain to not audit.
##	</summary>
## </param>
## <infoflow type="none"/>
#
interface(`corenet_dontaudit_udp_sendrecv_$1_port',`
	refpolicywarn(`dollarszero() has been deprecated, please remove.')
')

########################################
## <summary>
##	Bind TCP sockets to the $1 port.
## </summary>
## <param name="domain">
##	<summary>
##	Domain allowed access.
##	</summary>
## </param>
## <infoflow type="none"/>
#
interface(`corenet_tcp_bind_$1_port',`
	gen_require(`
		$3 $1_$2;
	')

	allow dollarsone $1_$2:tcp_socket name_bind;
	$4
')

########################################
## <summary>
##	Bind UDP sockets to the $1 port.
## </summary>
## <param name="domain">
##	<summary>
##	Domain allowed access.
##	</summary>
## </param>
## <infoflow type="none"/>
#
interface(`corenet_udp_bind_$1_port',`
	gen_require(`
		$3 $1_$2;
	')

	allow dollarsone $1_$2:udp_socket name_bind;
	$4
')

########################################
## <summary>
##	Make a TCP connection to the $1 port.
## </summary>
## <param name="domain">
##	<summary>
##	Domain allowed access.
##	</summary>
## </param>
#
interface(`corenet_tcp_connect_$1_port',`
	gen_require(`
		$3 $1_$2;
	')

	allow dollarsone $1_$2:tcp_socket name_connect;
')
'') dnl end create_port_interfaces

define(`create_packet_interfaces',``
########################################
## <summary>
##	Send $1 packets.
## </summary>
## <param name="domain">
##	<summary>
##	Domain allowed access.
##	</summary>
## </param>
## <infoflow type="write" weight="10"/>
#
interface(`corenet_send_$1_packets',`
	gen_require(`
		type $1_packet_t;
	')

	allow dollarsone $1_packet_t:packet send;
')

########################################
## <summary>
##	Do not audit attempts to send $1 packets.
## </summary>
## <param name="domain">
##	<summary>
##	Domain to not audit.
##	</summary>
## </param>
## <infoflow type="none"/>
#
interface(`corenet_dontaudit_send_$1_packets',`
	gen_require(`
		type $1_packet_t;
	')

	dontaudit dollarsone $1_packet_t:packet send;
')

########################################
## <summary>
##	Receive $1 packets.
## </summary>
## <param name="domain">
##	<summary>
##	Domain allowed access.
##	</summary>
## </param>
## <infoflow type="read" weight="10"/>
#
interface(`corenet_receive_$1_packets',`
	gen_require(`
		type $1_packet_t;
	')

	allow dollarsone $1_packet_t:packet recv;
')

########################################
## <summary>
##	Do not audit attempts to receive $1 packets.
## </summary>
## <param name="domain">
##	<summary>
##	Domain allowed access.
##	</summary>
## </param>
## <infoflow type="none"/>
#
interface(`corenet_dontaudit_receive_$1_packets',`
	gen_require(`
		type $1_packet_t;
	')

	dontaudit dollarsone $1_packet_t:packet recv;
')

########################################
## <summary>
##	Send and receive $1 packets.
## </summary>
## <param name="domain">
##	<summary>
##	Domain allowed access.
##	</summary>
## </param>
## <infoflow type="both" weight="10"/>
#
interface(`corenet_sendrecv_$1_packets',`
	corenet_send_$1_packets(dollarsone)
	corenet_receive_$1_packets(dollarsone)
')

########################################
## <summary>
##	Do not audit attempts to send and receive $1 packets.
## </summary>
## <param name="domain">
##	<summary>
##	Domain to not audit.
##	</summary>
## </param>
## <infoflow type="none"/>
#
interface(`corenet_dontaudit_sendrecv_$1_packets',`
	corenet_dontaudit_send_$1_packets(dollarsone)
	corenet_dontaudit_receive_$1_packets(dollarsone)
')

########################################
## <summary>
##	Relabel packets to $1 the packet type.
## </summary>
## <param name="domain">
##	<summary>
##	Domain allowed access.
##	</summary>
## </param>
#
interface(`corenet_relabelto_$1_packets',`
	gen_require(`
		type $1_packet_t;
	')

	allow dollarsone $1_packet_t:packet relabelto;
')
'') dnl end create_port_interfaces

define(`create_ibpkey_interfaces',``
########################################
## <summary>
##	Access the infiniband fabric on the $1 ibpkey.
## </summary>
## <param name="domain">
##	<summary>
##	Domain allowed access.
##	</summary>
## </param>
## <infoflow type="both" weight="10"/>
#
interface(`corenet_ib_access_$1_pkey',`
	gen_require(`
		$3 $1_$2;
	')

	allow dollarsone $1_$2:infiniband_pkey access;
')
'') dnl end create_ibpkey_interfaces

define(`create_ibendport_interfaces',``
########################################
## <summary>
##	Manage the subnet on $1 ibendport.
## </summary>
## <param name="domain">
##	<summary>
##	Domain allowed access.
##	</summary>
## </param>
## <infoflow type="both" weight="10"/>
#
interface(`corenet_ib_manage_subnet_$1_endport',`
	gen_require(`
		$3 $1_$2;
	')

	allow dollarsone $1_$2:infiniband_endport manage_subnet;
')
'') dnl end create_ibendport_interfaces

#
# create_netif_*_interfaces(linux_interfacename)
#
define(`create_netif_type_interfaces',`
create_netif_interfaces($1,netif_t,type)
')
define(`create_netif_type_interfaces_controlled',`
create_netif_interfaces_controlled($1,netif_t,type)
')
define(`create_netif_attrib_interfaces',`
create_netif_interfaces($1,netif,attribute)
')
define(`create_netif_attrib_interfaces_controlled',`
create_netif_interfaces_controlled($1,netif,attribute)
')

#
# network_interface(linux_interfacename,mls_sensitivity)
#
define(`network_interface',`
create_netif_type_interfaces($1)
')

define(`network_interface_controlled',`
create_netif_type_interfaces_controlled($1)
')

#
# create_node_*_interfaces(node_name)
#
define(`create_node_type_interfaces',`
create_node_interfaces($1,node_t,type)
')
define(`create_node_attrib_interfaces',`
create_node_interfaces($1,node,attribute)
')

#
# network_node(node_name,mls_sensitivity,address,netmask)
#
define(`network_node',`
create_node_type_interfaces($1)
')

# These next three macros have formatting, and should not be indented
define(`determine_reserved_capability',`dnl
ifelse($2,`',`',`dnl
ifelse(eval($2 < 1024),1,``allow' dollarsone self:capability net_bind_service;',`dnl
determine_reserved_capability(shiftn(3,$*))dnl
')dnl end inner ifelse
')dnl end outer ifelse
') dnl end determine reserved capability

#
# create_port_*_interfaces(port_name, protocol,portnum,mls_sensitivity [,protocol portnum mls_sensitivity[,...]])
# (these wrap create_port_interfaces to handle attributes and types)
define(`create_port_type_interfaces',`create_port_interfaces($1,port_t,type,determine_reserved_capability(shift($*)))')
define(`create_port_attrib_interfaces',`create_port_interfaces($1,port,attribute,determine_reserved_capability(shift($*)))')

#
# network_port(port_name,protocol portnum mls_sensitivity [,protocol,portnum,mls_sensitivity[,...]])
#
define(`network_port',`
create_port_type_interfaces($*)
create_packet_interfaces($1_client)
create_packet_interfaces($1_server)
')

#
# network_packet(packet_name)
#
define(`network_packet',`
create_packet_interfaces($1_client)
create_packet_interfaces($1_server)
')

#
# network_packet_simple(packet_name)
#
define(`network_packet_simple',`
create_packet_interfaces($1)
')

# create_ibpkey_*_interfaces(name, subnet_prefix, pkeynum,mls_sensitivity)
# (these wrap create_port_interfaces to handle attributes and types)
define(`create_ibpkey_type_interfaces',`create_ibpkey_interfaces($1,ibpkey_t,type,determine_reserved_capability(shift($*)))')

#
# ib_pkey(name,subnet_prefix pkeynum mls_sensitivity)
#
define(`ib_pkey',`
create_ibpkey_type_interfaces($*)
')

# create_ibendport_*_interfaces(name, devname, portnum,mls_sensitivity)
# (these wrap create_port_interfaces to handle attributes and types)
define(`create_ibendport_type_interfaces',`create_ibendport_interfaces($1,ibendport_t,type,determine_reserved_capability(shift($*)))')

#
# ib_endport(name,device_name, portnum mls_sensitivity)
#
define(`ib_endport',`
create_ibendport_type_interfaces($*)
')
