#include <unistd.h>
#include <fcntl.h>
#include <string.h>
#include <stdlib.h>
#include <errno.h>
#include <ctype.h>
#include <asm/page.h>
#include <stdio.h>
#include <dlfcn.h>

#include "dso.h"
#include "policy.h"
#include "selinux_internal.h"

char *selinux_mnt = NULL;

static void init_selinuxmnt(void)
{
	char *buf, *bufp, *p;
	size_t size;
	FILE *fp;

	if (selinux_mnt)
		return;

	fp = fopen("/proc/mounts", "r");
	if (!fp)
		return;

	size = PAGE_SIZE;
	buf = malloc(size);
	if (!buf)
		goto out;
		
	memset(buf, 0, size);

	while(( bufp = fgets_unlocked(buf, size, fp)))
	{
		char *tmp;
		p = strchr(buf, ' ');
		if (!p)
			goto out2;
		p++;
		tmp = strchr(p, ' ');
		if (!tmp)
			goto out2;
		if(!strncmp(tmp + 1, "selinuxfs ", 10)) {
			*tmp = '\0';
			break;
		}
	}

	if (!bufp)
		goto out2;

	selinux_mnt = strdup(p);

out2:
	free(buf);
out:
	fclose(fp);
	return;

}

static void fini_selinuxmnt(void)
{
	free(selinux_mnt);
	selinux_mnt = NULL;
}

void set_selinuxmnt(char *mnt)
{
	selinux_mnt = strdup(mnt);
}
hidden_def(set_selinuxmnt)
 
int context_translations hidden;
void *translation_lib_handle hidden;

/* from libsetrans.c */
extern int hidden (*lib_trans_to_raw_context)(char *trans, char **rawp);
extern int hidden (*lib_raw_to_trans_context)(char *raw, char **transp);


static void init_translations(void)
{
#ifdef SHARED
	int (*lib_trans_init)(void) = NULL;

	translation_lib_handle = dlopen("libsetrans.so.0", RTLD_NOW);
	if (!translation_lib_handle)
		return;

	dlerror();

	lib_trans_init = dlsym(translation_lib_handle,
	                       "init_context_translations");
	if (dlerror() || lib_trans_init())
		return;

	lib_raw_to_trans_context = dlsym(translation_lib_handle,
	                                 "translate_context");
	if (dlerror())
		return;

	lib_trans_to_raw_context = dlsym(translation_lib_handle,
	                                 "untranslate_context");
	if (dlerror())
		return;

	context_translations = 1;
#endif
}

static void fini_translations(void)
{
#ifdef SHARED
	context_translations = 0;
	if (translation_lib_handle) {
		dlclose(translation_lib_handle);
		translation_lib_handle = NULL;
	}
#endif
}

static void init_lib(void) __attribute__ ((constructor));
static void init_lib(void)
{
	init_selinuxmnt();
	init_translations();
}

static void fini_lib(void) __attribute__ ((destructor));
static void fini_lib(void)
{
	fini_translations();
	fini_selinuxmnt();
}
