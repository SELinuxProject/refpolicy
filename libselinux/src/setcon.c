/*
 * Author: Trusted Computer Solutions, Inc. <chanson@trustedcs.com>
 */

#include <unistd.h>
#include <fcntl.h>
#include <string.h>
#include "selinux_internal.h"

int setcon_raw(security_context_t context)
{
	int fd;
	ssize_t ret;

	fd = open("/proc/self/attr/current", O_RDWR);
	if (fd < 0)
		return -1;
	if (context) 
		ret = write(fd, context, strlen(context)+1);
	else
		ret = -1; /* we can not clear this one */
	close(fd);
	if (ret < 0)
		return -1;
	else
		return 0;
}
hidden_def(setcon_raw)

int setcon(char *context)
{
	int ret;
	security_context_t rcontext = context;

	if (context_translations && trans_to_raw_context(context, &rcontext))
		return -1;

 	ret = setcon_raw(rcontext);

	if (context_translations)
		freecon(rcontext);

	return ret;
}
