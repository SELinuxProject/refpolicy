#include <unistd.h>
#include <fcntl.h>
#include <string.h>
#include "selinux_internal.h"
#include <stdlib.h>
#include <errno.h>
#include <asm/page.h>
#include "policy.h"

int getcon_raw(security_context_t *context)
{
	char *buf;
	size_t size;
	int fd;
	ssize_t ret;

	fd = open("/proc/self/attr/current", O_RDONLY);
	if (fd < 0)
		return -1;

	size = PAGE_SIZE;
	buf = malloc(size);
	if (!buf) {
		ret = -1;
		goto out;
	}
	memset(buf, 0, size);

	ret = read(fd, buf, size-1);
	if (ret < 0)
		goto out2;

	*context = strdup(buf);
	if (!(*context)) {
		ret = -1;
		goto out2;
	}
	ret = 0;
out2:			
	free(buf);
out:
	close(fd);
	return ret;
}
hidden_def(getcon_raw)

int getcon(security_context_t *context)
{
	int ret;
	security_context_t rcontext;

 	ret = getcon_raw(&rcontext);

	if (context_translations && !ret) {
		if (raw_to_trans_context(rcontext, context)) {
			*context = NULL;
			ret = -1;
		}
		freecon(rcontext);
	} else if (!ret)
		*context = rcontext;

	return ret;
}
hidden_def(getcon)
