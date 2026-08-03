# Reference Policy Style Guide

All modules in Reference Policy should follow the following style
guidelines.

## **Modulename.te files**

The TE rule files should be have the following organization:

1. Declarations
2. Local policy rules
3. Unconfined access rules

### Declarations

This section has all of the declarations for the module. This section
has the following subsections:

1. Boolean declarations
2. Tunable declarations
3. Attribute declarations
4. Type declarations (including calls to templates that create types)

Notes:

- Each of these subsections should be alphabetically sorted by symbol
  name.
- A domain and its entrypoint file type (if declared in this module)
  should be grouped.
- Transform interface calls, such as domain\_type() and file\_type()
  should be grouped with the corresponding type declaration.

### Local policy rules

Each domain should have its own subsection. For each domain the rules
should be organized in the following matter:

1. self rules, starting with capability and process object classes
2. rules whose object is owned by this module (raw allow rules and
  policy patterns), sorted by object type
3. calls to other modules, sorted in alphabetical order
4. blocks, whose contents are sorted as above,
    1. build option blocks, sorted by build option name (e.g.,
       distro\_redhat)
    2. conditional policy blocks, sorted by Boolean name
    3. tunable policy blocks, sorted by tunable name
    4. optional policy blocks, sorted by the name of the module being
       called

Note: A module can call its own interfaces. It is preferred that an
interface not be created for internal-only use unless it's a complicated
concept that is being abstracted.

### Unconfined access rules

These rules follow the same rules as the local policy rules.

## **Modulename.if files**

The interfaces should follow the
[InterfaceNaming](INTERFACE_NAMING.md) guidelines.
The interface files should be organized in the following manner:

1. Templates
2. Transform interfaces
3. Access interfaces
4. Admin interfaces
5. Unconfined interface

### Transform interfaces

These are the interfaces that add a meaning to a type, such as
init\_daemon\_domain() and file\_type(). They should be sorted in the
following manner:

1. alphabetically by primary object type or attribute

### Access interfaces

1. alphabetically by primary object type or attribute, then
2. increasing in access (getattr, then setattr, read, append, write,
  rw, create, rename, delete, manage, relabelto, relabelfrom,
  relabel), then
3. if an allow and dontaudit interface exist for a particular access
  (e.g., modulename\_read\_foo() and
  modulename\_dontaudit\_read\_foo()), the allow interface is before
  the dontaudit interface.

#### Admin interfaces

- If there are multiple admin interfaces (e.g.
  modulename\_admin\_foo() and modulename\_admin\_bar()), such as for
  administrating a component of a module, the subcomponent admin
  interfaces should be sorted by component name.
- If there is an admin interface to administrate everything (e.g.
  modulename\_admin()), it should be the last interface in this
  section.

#### Unconfined interface

If there is an interface which provides unconfined access to a module's
resource, it should be the last interface in the file.

## **Modulename.fc** files

The file context entries should be sorted in the following manner:

1. alphabetically by path, then
2. by increasing depth, then
3. entries with metacharacters (**.\***, **?**, **[a-z]**, etc.) first
   and exact matches last
