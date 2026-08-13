# Reference Policy Interface and Template Naming Conventions

All Reference Policy interfaces and templates should use the following
naming convention.

```text
modulename[_modifier]_verb_predicate()
```

* modulename: The name of the module, or for modules with long names, an abbreviation of the
module name. If an abbreviation is used, it must be consistent throughout the module. e.g.,
apache, samba, and corenet (for corenetwork).
* modifier: Describe variations of a common interface. The most common use is the modifier
dontaudit. (optional)

## Common File Interface Elements

These are applicable for all file object classes (file, lnk\_file,
sock\_file, fifo\_file, blk\_file, chr\_file).

### File Verbs

* getattr: Get the attributes of an object, such as stat().
* setattr: Set the attributes of an object, such as chmod().
* read: Read an object.
* mmap_read: Memory map an object as read-only.
* append: Append only to an object.
* write: Write an object. (append is implied)
* rw: Read and write an object.
* mmap_rw: Memory map an object as read-write.
* create: Create an object.
* delete: Delete an object.
* manage: Create, read, write, and delete an object.
* mmap_manage: Create and delete an object and memory map an object as read-write.
* relabelfrom: Relabel from the object's type
* relabelto: Relabel to the object's type
* relabel: Relabel to and from the object's type
* exec: Execute a file in the caller's domain (no domain transition; file object class only).
* mmap_exec: Memory map a file as read-only and executable

### File Predicates

The predicate is usually derived on the object's type, such as smbd_tmp_files. In general they
should also be plural (tmp_file**s**, not tmp_file), since the policy normally can't enforce a
label existing on single objects.

## Common Directory Interface Elements

### Directory Verbs

* getattr: Get the attributes of a directory.
* setattr: Set the attributes of a directory.
* search: Search a directory, but not get a list of directory entries.
* list: Read the list of directory entries.
* rw: Add and remove directory entries.
* manage: Add and remove directory entries, create and delete directories.
* mounton: Filesystems can be mounted on this directory.

### Directory Predicates

The predicate is usually derived on the object's type, such as smbd_tmp_dirs. In general they
should also be plural (tmp_dir**s**, not tmp_dir), since the policy normally can't enforce a label
existing on single objects.

## Common Process Interface Elements

### Process Verbs

* sigchld: Send a SIGCHLD signal.
* sigstop: Send a SIGSTOP signal.
* signull: Send a null signal.
* kill: Send a kill signal (SIGKILL).
* domtrans: Execute a program and perform a domain transition.
* run: Execute a program and perform a domain transition. Allow the target domain to read and
write the specified terminal, and allow the specified role the target domain. This is used with
interactive programs.

### Process Predicates

The predicate of process interfaces usually is the common name of the
domain, e.g., smbd or nmbd.

## Common Networking Interface Elements

### Modifiers

* tcp: Internet domain TCP sockets
* udp: Internet domain UCP sockets
* raw: Internet domain raw IP sockets
* stream: Unix domain stream sockets
* dgram: Unix domain datagram sockets

### Networking Verbs

* send: Send network traffic on the network object.
* receive: Receive network traffic on the network object.
* sendrecv: Send and receive network traffic on the network object.
* bind: Bind a socket to a port or node.
* connect: Connect to another process or port.

### Networking Predicates

* if: Network interfaces
* nodes: Network nodes
* ports: Network ports
* packets: Network packets

## Common Filesystem Interface Elements

### Filesystem Verbs

* getattr: Get the attributes of the filesystem
* mount: Mount the filesystem
* unmount: Unmount the filesystem
* remount: Remount the filesystem (change mount options)
* associate: Associate a file type to the filesystem

### Filesystem Predicates

The predicate of filesystem interfaces is usually the filesystem type,
e.g., tmpfs or cifs.
