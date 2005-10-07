#include <unistd.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <errno.h>
#include <syslog.h>
#include <pwd.h>
#include <selinux/selinux.h>
#include <errno.h>

int permanent = 0;

int setbool(char **list, size_t start, size_t end);


void usage(void)
{
	fputs("\nUsage:  setsebool [ -P ] boolean value | bool1=val1 bool2=val2...\n\n", stderr);
	exit(1);
}

int main(int argc, char **argv)
{
	size_t rc, start;

	if (argc < 2) 
		usage();

	if (is_selinux_enabled() <= 0) {
		fputs("setsebool:  SELinux is disabled.\n", stderr);
		return 1;
	}

	if (strcmp(argv[1], "-P") == 0) {
		permanent = 1;
		if (argc < 3) 
			usage();
		start = 2;
	}
	else
		start = 1;

	/* Check to see which way we are being called. If a '=' is passed,
	   we'll enforce the list syntax. If not we'll enforce the original
	   syntax for backward compatibility. */
	if (strchr(argv[start], '=') == 0) {
		int len;
		char *bool_list[1];

		if ((argc - start) != 2)
			usage();

		/* Add 1 for the '=' */
		len = strlen(argv[start]) + strlen(argv[start+1]) + 2;
		bool_list[0]=(char *)malloc(len);
		if (bool_list[0] == 0) {
			fputs("Out of memory - aborting\n", stderr);
			return 1;
		}
		snprintf(bool_list[0], len, "%s=%s", argv[start], 
							argv[start+1]);
		rc = setbool(bool_list, 0, 1);
		free(bool_list[0]);
	}
	else 
		rc = setbool(argv, start, argc);

	return rc;
}

/* Given an array of strings in the form "boolname=value", a start index,
   and a finish index...walk the list and set the bool. */
int setbool(char **list, size_t start, size_t end)
{
	char *name, *value_ptr;
	int i=start, value;
	int ret=0;
	int j=0;
	size_t boolcnt=end-start;
	struct passwd *pwd;
	SELboolean *vallist=calloc(boolcnt, sizeof(SELboolean));
	if (!vallist) {
		fprintf(stderr, 
			"Error setting booleans: %s\n", strerror(errno));
		return 1;
	}
	while (i < end) {
		name = list[i];
		value_ptr = strchr(list[i], '=');
		if (value_ptr == 0) {
			fprintf(stderr, 
			"setsebool: '=' not found in boolean expression %s\n",
				list[i]);
			ret=4;
			goto error_label;
		}
		*value_ptr = 0;
		value_ptr++;
		if (strcmp(value_ptr, "1") == 0 || 
				strcasecmp(value_ptr, "true") == 0)
			value = 1;
		else if (strcmp(value_ptr, "0") == 0 || 
				strcasecmp(value_ptr, "false") == 0)
			value = 0;
		else {
			fprintf(stderr, "setsebool: illegal boolean value %s\n",
				value_ptr);
			ret=1;
			goto error_label;
		}

		vallist[j].value = value;
		vallist[j].name = strdup(name);
		if (!vallist[j].name) {
			fprintf(stderr, 
				"Error setting boolean %s to value %d (%s)\n", 
				name, value, strerror(errno));
			ret= 2;
			goto error_label;
		}
		i++;
		j++;

		/* Now put it back */
		value_ptr--;
		*value_ptr = '=';
	}

	ret=security_set_boolean_list(boolcnt, vallist, permanent);

 error_label:
	for (i=0; i < boolcnt; i++) 
		if (vallist[i].name) free(vallist[i].name);
	free(vallist);

	if (ret) {
		if (errno==ENOENT) {
			fprintf(stderr, 
				"Error setting boolean: Invalid boolean\n");
		} else {
			if (errno) 
				perror("Error setting booleans");
		}
		return ret;
	}

	/* Now log what was done */
	pwd = getpwuid(getuid());
	i = start;
	while (i < end) {
		/* Error checking shouldn't be needed since we just did
		   this above and aborted if something went wrong. */
		name = list[i];
		value_ptr = strchr(name, '=');
		*value_ptr = 0;
		value_ptr++;
		if (pwd && pwd->pw_name)
			syslog(LOG_NOTICE, 
			    "The %s policy boolean was changed to %s by %s",
				name, value_ptr, pwd->pw_name);
		else
			syslog(LOG_NOTICE, 
			    "The %s policy boolean was changed to %s by uid:%d",
				name, value_ptr, getuid());
		i++;
	}

	return 0;
}

