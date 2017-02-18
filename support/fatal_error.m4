ifdef(`m4_fatal_error',`
    ifdef(`m4_werror',`errprint(__file__: Notice: Treating warnings as errors.__endline__)')
    m4exit(`1')
')
