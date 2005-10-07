#include <unistd.h>
#include <fcntl.h>
#include <string.h>
#include <selinux/flask.h>
#include "selinux_internal.h"
#include "context_internal.h"

int rpm_execcon(unsigned int verified __attribute__((unused)), 
		const char *filename, 
		char *const argv[], char *const envp[])
{
	security_context_t mycon = NULL, fcon = NULL, newcon = NULL;
	context_t con = NULL;
	int rc;

	if (is_selinux_enabled() < 1)
		return execve(filename, argv, envp);

	rc = getcon(&mycon);
	if (rc < 0)
		goto out;

	rc = getfilecon(filename, &fcon);
	if (rc < 0)
		goto out;

	rc = security_compute_create(mycon, fcon, SECCLASS_PROCESS, &newcon);
	if (rc < 0)
		goto out;

	if (!strcmp(mycon, newcon)) {
		/* No default transition, use rpm_script_t for now. */
		con = context_new(mycon);
		if (!con)
			goto out;
		if (context_type_set(con, "rpm_script_t"))
			goto out;
		freecon(newcon);
		newcon = strdup(context_str(con));
		if (!newcon)
			goto out;
	}

	rc = setexeccon(newcon);
	if (rc < 0) 
		goto out;
	rc = execve(filename, argv, envp);
out:
	context_free(con);
	freecon(newcon);
	freecon(fcon);
	freecon(mycon);
	return rc < 0 ? rc : 0;
}
