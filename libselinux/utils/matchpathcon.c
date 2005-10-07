#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <getopt.h>
#include <selinux/selinux.h>

void usage(const char *progname) 
{
	fprintf(stderr, "usage:  %s [-n] path...\n", progname);
	exit(1);
}

int main(int argc, char **argv) 
{
	char *buf;
	int rc, i;
	int header=1, opt;

	if (argc < 2) usage(argv[0]);

	while ((opt = getopt(argc, argv, "n")) > 0) {
		switch (opt) {
		case 'n':
			header=0;
			break;
		default:
			usage(argv[0]);
		}
	}
	for (i = optind; i < argc; i++) {
		rc = matchpathcon(argv[i], 0, &buf);
		if (rc < 0) {
			fprintf(stderr, "%s:  matchpathcon(%s) failed\n", argv[0], argv[i]);
			return 2;
		}
		if (header)
			printf("%s\t%s\n", argv[i], buf);
		else
			printf("%s\n", buf);

		freecon(buf);
	}
	return 0;
}
