#include <unistd.h>
#include <fcntl.h>
#include <string.h>
#include <stdlib.h>
#include <errno.h>
#include <sys/xattr.h>
#include "selinux_internal.h"
#include "policy.h"

int fgetfilecon_raw(int fd, security_context_t *context)
{
	char *buf;
	ssize_t size;
	ssize_t ret;

	size = INITCONTEXTLEN+1;
	buf = malloc(size);
	if (!buf) 
		return -1;
	memset(buf, 0, size);

	ret = fgetxattr(fd, XATTR_NAME_SELINUX, buf, size-1);
	if (ret < 0 && errno == ERANGE) {
		char *newbuf;

		size = fgetxattr(fd, XATTR_NAME_SELINUX, NULL, 0);
		if (size < 0)
			goto out;

		size++;
		newbuf = realloc(buf, size);
		if (!newbuf)
			goto out;

		buf = newbuf;
		memset(buf, 0, size);
		ret = fgetxattr(fd, XATTR_NAME_SELINUX, buf, size-1); 
	}
out:			
	if (ret < 0)
		free(buf);
	else
		*context = buf;
	return ret;
}
hidden_def(fgetfilecon_raw)

int fgetfilecon(int fd, security_context_t *context)
{
	security_context_t rcontext;
	int ret;

 	ret = fgetfilecon_raw(fd, &rcontext);

	if (context_translations && ret > 0) {
		if (raw_to_trans_context(rcontext, context)) {
			*context = NULL;
			ret = -1;
		}
		freecon(rcontext);
	} else if (ret > 0)
		*context = rcontext;

	return ret;
}
