# Getting Started with Reference Policy

This guide will walk you through the basics of creating a new reference
policy module. This will also serve as an introduction to the basic
concepts and philosophy of refpolicy.

## Creating A Module

Modules are the principal organizing component in refpolicy. A module
contains the policy for an application or related group of applications,
private and shared resources, labeling information, and interfaces that
allow other modules access to the module's resources. The majority of the
global policy has been eliminated in refpolicy. Certain policy
components, like users and object classes, are still global in
refpolicy, but almost all TE policy is now contained within a module.

Let's create a new module called `myapp`. This is done by creating three
files: `myapp.te`, `myapp.fc`, and `myapp.if`. The file `myapp.te` will
contain all of the policy private to this module, including any types or
attributes. The file `myapp.fc` file will contain the file context
labeling statements for this module. Finally, the file `myapp.if` will
contain the interfaces for this module (interfaces will be explained
below).

### Module TE Policy {#ModuleTEPolicy}

First create `myapp.te` and add the following:

``` {.wiki}
policy_module(myapp,1.0)

# Private type declarations
type myapp_t;
type myapp_exec_t;
type myapp_log_t;
type myapp_tmp_t;

domain_type(myapp_t)
domain_entry_file(myapp_t, myapp_exec_t)
logging_log_file(myapp_log_t)
files_tmp_file(myapp_tmp_t)
```

This creates all of the types needed for this module, including a type
for the process, executables, log files, and temporary files. The first
thing to notice is that there are no attributes applied to any of these
types. In refpolicy all types and attributes can only be referred to in
the module that declares them. This means that it is not possible, for
example, to directly refer to the domain attribute. Instead, macros in
other modules are used to declare that a type will be used for a certain
purpose. These macros will likely use attributes (but not necessarily),
but it allows the module that declared the attribute to strictly control
how it can be used. In this example interfaces are used to transform the
types into a domain, entry file, log file, and temporary file.

Let's expand this example further by allowing some access for these
types. My application needs access between its own types and access to
read random numbers. The access between private types is written exactly
the same way current policy rules are written, i.e.:

``` {.wiki}
allow myapp_t myapp_log_t:file append_file_perms;
allow myapp_t myapp_tmp_t:file manage_file_perms;
```

This allows myapp\_t to write to its private types, but it needs to be
able to create its temporary files in /tmp. This requires a call to the
files module.

``` {.wiki}
files_tmp_filetrans(myapp_t,myapp_tmp_t,file)
```

This call to the files module allows myapp\_t to create myapp\_tmp\_t
files in the /tmp directory.

### Module FC Policy {#ModuleFCPolicy}

The file contexts file lists files and the labels they should have.
Create myapp.fc and add the following:

``` {.wiki}
/usr/bin/myapp    --  gen_context(system_u:object_r:myapp_exec_t,s0)
```

The gen\_context() macro has three parameters, the base SELinux label,
the MLS level, and optionally the MCS category. When compiling a module,
the macro will add the appropriate MLS/MCS part to the label when
needed. In the above example, the file will have a level of s0 when
compiled for a MLS policy, and no categories when compiled for MCS. If
the level s5:c1 is needed for MLS, and category c0 is needed for MCS,
the above line would become:

``` {.wiki}
/usr/bin/myapp    --  gen_context(system_u:object_r:myapp_exec_t,s5:c1,c0)
```

Since the MCS policy has only one sensitivity (s0), this is
automatically added by the gen\_context() macro, and should not be added
by the user. The raw category set must be specified, instead of the
translated category set (e.g.,
"SystemLow-SystemHigh").

### Module IF Policy {#ModuleIFPolicy}

The interface file creates the macros that other modules will use to
gain access to my resources. This allows the module that created the
type or attribute to define appropriate uses. Additionally, it provides
a single point for documentation. Create myapp.if and add the following:

``` {.wiki}
## <summary>Myapp example policy</summary>
## <desc>
##  <p>
##      More descriptive text about myapp.  The desc
##      tag can also use p, ul, and ol
##      html tags for formatting.
##  </p>
##  <p>
##      This policy supports the following myapp features:
##      <ul>
##      <li>Feature A</li>
##      <li>Feature B</li>
##      <li>Feature C</li>
##      </ul>
##  </p>
## </desc>

########################################
## <summary>
##  Execute a domain transition to run myapp.
## </summary>
## <param name="domain">
##  <summary>
##  Domain allowed to transition.
##  </summary>
## </param>

interface(`myapp_domtrans',`
    gen_requires(`
        type myapp_t, myapp_exec_t;
    ')

    domtrans_pattern($1,myapp_exec_t,myapp_t)
')

########################################
## <summary>
##  Read myapp log files.
## </summary>
## <param name="domain">
##  <summary>
##  Domain allowed to read the log files.
##  </summary>
## </param>

interface(`myapp_read_log',`
    gen_requires(`
        type myapp_log_t;
    ')

    logging_search_logs($1)
    allow $1 myapp_log_t:file read_file_perms;
')
```

The first interface allows other domains to do a domain transition to
myapp\_t, by executing a program labeled myapp\_exec\_t.

The second interface allows other domains to read myapp's log files.
Myapp's log files are in the /var/log directory, so the access to search
the /var/log directory is also given by the interface. The
gen\_requires() macro is used to support loadable policy modules, and
must explicitly list the type and attributes used by this interface. If
object classes of a userland object manager are used, the class and the
permissions used by the interface must also be listed.

## Compiling Modules

Two methods of building modules are supported, headers and complete
source. Current systems, that is Fedora Core 5 or newer, which support loadable
policy modules should compile modules using headers. Using the complete
source for building modules is only needed if loadable modules are not
supported on the system or when doing other modifications to the base
policy. Generally this is only suggested for experts.

## Building Using Policy Headers

When building a loadable policy module, the three module source files
need not be in a specific directory. A development directory in the
user's home directory would be sufficient. In this example, lets place
it in the policy directory in the home directory. The example Makefile
should be copied to this directory. It is usually located in the
/usr/share/doc/PKGNAME directory, where PKGNAME is the name of the
policy package that has the policy headers.

``` {.wiki}
$ cp /usr/share/doc/refpolicy-20060307/Makefile.example ~/policy/Makefile
```

Alternatively, this can be copied [from the Reference Policy source](https://github.com/SELinuxProject/refpolicy/blob/master/doc/Makefile.example), from
the doc directory. The Makefile is not required, but will simplify the
process.

Now the policy directory should have the three module source files and
Makefile. All that needs to be done is to run make, and the policy will
be compiled.

``` {.wiki}
$ make
Compiling targeted myapp module
/usr/bin/checkmodule:  loading policy configuration from tmp/myapp.tmp
/usr/bin/checkmodule:  policy configuration loaded
/usr/bin/checkmodule:  writing binary representation (version 5) to tmp/myapp.mod
Creating targeted myapp.pp policy package
```

If you do not have the example Makefile, you must tell make where to
find the policy header's Makefile, by using the -f option. The Makefile
for the base policy provided by the Linux distribution should be found
in the /usr/share/selinux/NAME/include directory, where NAME is the name
of the policy, for example, strict or targeted.

``` {.wiki}
$ make -f /usr/share/selinux/targeted/include/Makefile
Compiling targeted myapp module
/usr/bin/checkmodule:  loading policy configuration from tmp/myapp.tmp
/usr/bin/checkmodule:  policy configuration loaded
/usr/bin/checkmodule:  writing binary representation (version 5) to tmp/myapp.mod
Creating targeted myapp.pp policy package
```

When this succeeds, there will be a `myapp.pp` policy package that can be
inserted into the running policy. To load the module, you must be running
as root, in a role allowed to run `semodule`. Then run `semodule -i` to
insert the module into the running policy:

``` {.wiki}
# semodule -i myapp.pp
```

The semodule command will only print messages if there is an error
inserting the module. If it succeeds, `semodule -l` should list the myapp
module, and the version:

``` {.wiki}
# semodule -l
myapp   1.0
```
