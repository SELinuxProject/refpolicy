#include <unistd.h>
#include <string.h>
#include <fcntl.h>
#include "selinux_internal.h"

int setfscreatecon_raw(char *context)
{
	int fd;
	ssize_t ret;

	fd = open("/proc/self/attr/fscreate", O_RDWR);
	if (fd < 0)
		return -1;
	if (context) 
		ret = write(fd, context, strlen(context)+1);
	else
		ret = write(fd, NULL, 0); /* clear */
	close(fd);
	if (ret < 0)
		return -1;
	else
		return 0;
}
hidden_def(setfscreatecon_raw)

int setfscreatecon(char *context)
{
	int ret;
	security_context_t rcontext = context;

	if (context_translations && trans_to_raw_context(context, &rcontext))
		return -1;

 	ret = setfscreatecon_raw(rcontext);

	if (context_translations)
		freecon(rcontext);

	return ret;
}
