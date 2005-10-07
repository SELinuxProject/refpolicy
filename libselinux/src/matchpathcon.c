#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <string.h>
#include "selinux_internal.h"
#include <stdio.h>
#include <stdio_ext.h>
#include <stdlib.h>
#include <ctype.h>
#include <errno.h>
#include <limits.h>
#include <regex.h>
#include <stdarg.h>
#include "policy.h"
#include "context_internal.h"

static void 
#ifdef __GNUC__
__attribute__ ((format (printf, 1, 2)))
#endif
default_printf(const char *fmt, ...) 
{
	va_list ap;
	va_start(ap, fmt);
	vfprintf(stderr, fmt, ap);
	va_end(ap);
}

/* If MLS is disabled, strip any MLS level field from the context.
   This allows file_contexts with MLS levels to be processed on
   a non-MLS system that otherwise has the same policy. */
static inline int STRIP_LEVEL(char **context, int mls_enabled)
{
	char *str;
	context_t con;
	int rc = -1;

	if (mls_enabled)
		return 0;

	con = context_new(*context);
	if (!con)
		return rc;

	if (context_range_set(con,NULL))
		goto out;

	str = context_str(con);
	if (!str)
		goto out;

	str = strdup(str);
	if (!str)
		goto out;

	free(*context);
	*context = str;
	rc = 0;
out:
	context_free(con);
	return rc;
}

static void (*myprintf)(const char *fmt, ...) = &default_printf;

void set_matchpathcon_printf(void (*f)(const char *fmt, ...))
{
	if (f)
		myprintf = f;
	else
		myprintf = &default_printf;
}

static int default_invalidcon(const char *path, unsigned lineno, char *context)
{
	if (security_check_context(context) < 0 && errno != ENOENT) {
		myprintf("%s:  line %u has invalid context %s\n", path, lineno, context);
		return 1;
	}
	return 0;
}

static int (*myinvalidcon)(const char *p, unsigned l, char *c) = &default_invalidcon;

void set_matchpathcon_invalidcon(int (*f)(const char *p, unsigned l, char *c))
{
	if (f)
		myinvalidcon = f;
	else
		myinvalidcon = &default_invalidcon;
}

static unsigned int myflags;

void set_matchpathcon_flags(unsigned int flags)
{
	myflags = flags;
}

/*
 * A file security context specification.
 */
typedef struct spec {
	char *regex_str;	/* regular expession string for diagnostic messages */
	char *type_str;		/* type string for diagnostic messages */
	char *context;		/* context string */
	regex_t regex;		/* compiled regular expression */
	mode_t mode;		/* mode format value */
	int matches;		/* number of matching pathnames */
	int hasMetaChars; 	/* indicates whether the RE has 
				   any meta characters.  
				   0 = no meta chars 
				   1 = has one or more meta chars */
	int stem_id;		/* indicates which of the stem-compression
				 * items it matches */
} spec_t;

typedef struct stem {
	char *buf;
	int len;
} stem_t;

static stem_t *stem_arr = NULL;
static int num_stems = 0;
static int alloc_stems = 0;

static const char * const regex_chars = ".^$?*+|[({";

/* Return the length of the text that can be considered the stem, returns 0
 * if there is no identifiable stem */
static int get_stem_from_spec(const char * const buf)
{
	const char *tmp = strchr(buf + 1, '/');
	const char *ind;

	if(!tmp)
		return 0;

	for(ind = buf; ind < tmp; ind++)
	{
		if(strchr(regex_chars, (int)*ind))
			return 0;
	}
	return tmp - buf;
}

/* return the length of the text that is the stem of a file name */
static int get_stem_from_file_name(const char * const buf)
{
	const char *tmp = strchr(buf + 1, '/');

	if(!tmp)
		return 0;
	return tmp - buf;
}

/* find the stem of a file spec, returns the index into stem_arr for a new
 * or existing stem, (or -1 if there is no possible stem - IE for a file in
 * the root directory or a regex that is too complex for us).  Makes buf
 * point to the text AFTER the stem. */
static int find_stem_from_spec(const char **buf)
{
	int i;
	int stem_len = get_stem_from_spec(*buf);

	if(!stem_len)
		return -1;
	for(i = 0; i < num_stems; i++)
	{
		if(stem_len == stem_arr[i].len && !strncmp(*buf, stem_arr[i].buf, stem_len))
		{
			*buf += stem_len;
			return i;
		}
	}
	if(num_stems == alloc_stems)
	{
		stem_t *tmp_arr;
		alloc_stems = alloc_stems * 2 + 16;
		tmp_arr = realloc(stem_arr, sizeof(stem_t) * alloc_stems);
		if(!tmp_arr)
			return -1;
		stem_arr = tmp_arr;
	}
	stem_arr[num_stems].len = stem_len;
	stem_arr[num_stems].buf = malloc(stem_len + 1);
	if(!stem_arr[num_stems].buf)
		return -1;
	memcpy(stem_arr[num_stems].buf, *buf, stem_len);
	stem_arr[num_stems].buf[stem_len] = '\0';
	num_stems++;
	*buf += stem_len;
	return num_stems - 1;
}

/* find the stem of a file name, returns the index into stem_arr (or -1 if
 * there is no match - IE for a file in the root directory or a regex that is
 * too complex for us).  Makes buf point to the text AFTER the stem. */
static int find_stem_from_file(const char **buf)
{
	int i;
	int stem_len = get_stem_from_file_name(*buf);

	if(!stem_len)
		return -1;
	for(i = 0; i < num_stems; i++)
	{
		if(stem_len == stem_arr[i].len && !strncmp(*buf, stem_arr[i].buf, stem_len))
		{
			*buf += stem_len;
			return i;
		}
	}
	return -1;
}

/*
 * The array of specifications, initially in the
 * same order as in the specification file.
 * Sorting occurs based on hasMetaChars
 */
static spec_t *spec_arr;
static unsigned int nspec;

/*
 * An association between an inode and a 
 * specification.  
 */
typedef struct file_spec {
	ino_t ino;		/* inode number */
	int specind;		/* index of specification in spec */
	char *file;		/* full pathname for diagnostic messages about conflicts */
	struct file_spec *next;	/* next association in hash bucket chain */
} file_spec_t;

/*
 * The hash table of associations, hashed by inode number.
 * Chaining is used for collisions, with elements ordered
 * by inode number in each bucket.  Each hash bucket has a dummy 
 * header.
 */
#define HASH_BITS 16
#define HASH_BUCKETS (1 << HASH_BITS)
#define HASH_MASK (HASH_BUCKETS-1)
static file_spec_t *fl_head;

/*
 * Try to add an association between an inode and
 * a specification.  If there is already an association
 * for the inode and it conflicts with this specification,
 * then use the specification that occurs later in the
 * specification array.
 */
int matchpathcon_filespec_add(ino_t ino, int specind, const char *file)
{
	file_spec_t *prevfl, *fl;
	int h, no_conflict, ret;
	struct stat sb;

	if (!fl_head) {
		fl_head = malloc(sizeof(file_spec_t)*HASH_BUCKETS);
		if (!fl_head)
			goto oom;
		memset(fl_head, 0, sizeof(file_spec_t)*HASH_BUCKETS);
	}

	h = (ino + (ino >> HASH_BITS)) & HASH_MASK;
	for (prevfl = &fl_head[h], fl = fl_head[h].next; fl;
	     prevfl = fl, fl = fl->next) {
		if (ino == fl->ino) {
			ret = lstat(fl->file, &sb);
			if (ret < 0 || sb.st_ino != ino) {
				fl->specind = specind;
				free(fl->file);
				fl->file = malloc(strlen(file) + 1);
				if (!fl->file)
					goto oom;
				strcpy(fl->file, file);
				return fl->specind;

			}

			no_conflict = (strcmp(spec_arr[fl->specind].context,spec_arr[specind].context) == 0);
			if (no_conflict)
				return fl->specind;

			myprintf("%s:  conflicting specifications for %s and %s, using %s.\n",
				__FUNCTION__, file, fl->file,
				((specind > fl->specind) ? spec_arr[specind].
				 context : spec_arr[fl->specind].context));
			fl->specind =
			    (specind >
			     fl->specind) ? specind : fl->specind;
			free(fl->file);
			fl->file = malloc(strlen(file) + 1);
			if (!fl->file)
				goto oom;
			strcpy(fl->file, file);
			return fl->specind;
		}

		if (ino > fl->ino)
			break;
	}

	fl = malloc(sizeof(file_spec_t));
	if (!fl)
		goto oom;
	fl->ino = ino;
	fl->specind = specind;
	fl->file = malloc(strlen(file) + 1);
	if (!fl->file)
		goto oom_freefl;
	strcpy(fl->file, file);
	fl->next = prevfl->next;
	prevfl->next = fl;
	return fl->specind;
oom_freefl:
	free(fl);
oom:
	myprintf("%s:  insufficient memory for file label entry for %s\n",
		 __FUNCTION__, file);
	return -1;
}

/*
 * Evaluate the association hash table distribution.
 */
void matchpathcon_filespec_eval(void)
{
	file_spec_t *fl;
	int h, used, nel, len, longest;

	if (!fl_head)
		return;

	used = 0;
	longest = 0;
	nel = 0;
	for (h = 0; h < HASH_BUCKETS; h++) {
		len = 0;
		for (fl = fl_head[h].next; fl; fl = fl->next) {
			len++;
		}
		if (len)
			used++;
		if (len > longest)
			longest = len;
		nel += len;
	}

	myprintf
	    ("%s:  hash table stats: %d elements, %d/%d buckets used, longest chain length %d\n",
	     __FUNCTION__, nel, used, HASH_BUCKETS, longest);
}

/*
 * Destroy the association hash table.
 */
void matchpathcon_filespec_destroy(void)
{
	file_spec_t *fl, *tmp;
	int h;

	if (!fl_head)
		return;

	for (h = 0; h < HASH_BUCKETS; h++) {
		fl = fl_head[h].next;
		while (fl) {
			tmp = fl;
			fl = fl->next;
			free(tmp->file);
			free(tmp);
		}
		fl_head[h].next = NULL;
	}
	free(fl_head);
	fl_head = NULL;
}

/*
 * Warn about duplicate specifications.
 */
static void nodups_specs(const char *path)
{
	unsigned int ii, jj;
	struct spec *curr_spec;

	for (ii = 0; ii < nspec; ii++) {
		curr_spec = &spec_arr[ii];
		for (jj = ii + 1; jj < nspec; jj++) { 
			if ((!strcmp(spec_arr[jj].regex_str, curr_spec->regex_str))
									&&
				(!spec_arr[jj].mode || !curr_spec->mode 
				 || spec_arr[jj].mode == curr_spec->mode)) {
				if (strcmp(spec_arr[jj].context, curr_spec->context)) {
					myprintf(
					"%s: Multiple different specifications for %s  (%s and %s).\n",
						path, curr_spec->regex_str, 
						spec_arr[jj].context,
						curr_spec->context);
				}
				else {
					myprintf(
					"%s: Multiple same specifications for %s.\n",
						path, curr_spec->regex_str);
				}
			}
		}
	}
}

/* Determine if the regular expression specification has any meta characters. */
static void spec_hasMetaChars(struct spec *spec)
{
	char *c;
	int len;
	char *end;

	c = spec->regex_str;
	len = strlen(spec->regex_str);
	end = c + len;

	spec->hasMetaChars = 0; 

	/* Look at each character in the RE specification string for a 
	 * meta character. Return when any meta character reached. */
	while (c != end) {
		switch(*c) {
			case '.':
			case '^':
			case '$':
			case '?':
			case '*':
			case '+':
			case '|':
			case '[':
			case '(':
			case '{':
				spec->hasMetaChars = 1;
				return;
			case '\\':		/* skip the next character */
				c++;
				break;
			default:
				break;

		}
		c++;
	}
	return;
}
static int process_line( const char *path, char *line_buf, int pass, unsigned lineno, int mls_enabled) {
	int items, len, regerr;
	char *buf_p;
	char *regex, *type, *context;
	char *anchored_regex;
	len = strlen(line_buf);
	if (line_buf[len - 1] == '\n')
		line_buf[len - 1] = 0;
	buf_p = line_buf;
	while (isspace(*buf_p))
		buf_p++;
	/* Skip comment lines and empty lines. */
	if (*buf_p == '#' || *buf_p == 0)
		return 0;
	items =
		sscanf(line_buf, "%as %as %as", &regex, &type,
		       &context);
	if (items < 2) {
		myprintf("%s:  line %d is missing fields\n, skipping", path, lineno); 
		return 0;
	} else if (items == 2) {
		/* The type field is optional. */
		free(context);
		context = type;
		type = 0;
	}
	
	if (pass == 1) {
		/* On the second pass, compile and store the specification in spec. */
		const char *reg_buf = regex;
		char *cp;
		spec_arr[nspec].stem_id = find_stem_from_spec(&reg_buf);
		spec_arr[nspec].regex_str = regex;
		
		/* Anchor the regular expression. */
		len = strlen(reg_buf);
		cp = anchored_regex = malloc(len + 3);
		if (!anchored_regex)
			return -1;
		/* Create ^...$ regexp.  */
		*cp++ = '^';
		cp = mempcpy(cp, reg_buf, len);
		*cp++ = '$';
		*cp = '\0';
		
		/* Compile the regular expression. */
		regerr =
			regcomp(&spec_arr[nspec].regex,
				anchored_regex,
				REG_EXTENDED | REG_NOSUB);
		if (regerr != 0) {
			size_t errsz = 0;
			char *errbuf = NULL;
			errsz = regerror(regerr, &spec_arr[nspec].regex, 
					 errbuf, errsz);
			if (errsz)
				errbuf = malloc(errsz);
			if (errbuf)
				(void) regerror(regerr, 
						&spec_arr[nspec].regex, 
						errbuf, errsz);
			myprintf("%s:  line %d has invalid regex %s:  %s\n", path, lineno, anchored_regex, (errbuf ? errbuf : "out of memory")); 
			free(anchored_regex);
			return 0;
		}
		free(anchored_regex);
		
		/* Convert the type string to a mode format */
		spec_arr[nspec].type_str = type;
		spec_arr[nspec].mode = 0;
		if (!type)
			goto skip_type;
		len = strlen(type);
		if (type[0] != '-' || len != 2) {
			myprintf("%s:  line %d has invalid file type %s\n", path, lineno, type); 
			return 0;
		}
		switch (type[1]) {
		case 'b':
			spec_arr[nspec].mode = S_IFBLK;
			break;
		case 'c':
			spec_arr[nspec].mode = S_IFCHR;
			break;
		case 'd':
			spec_arr[nspec].mode = S_IFDIR;
			break;
		case 'p':
			spec_arr[nspec].mode = S_IFIFO;
			break;
		case 'l':
			spec_arr[nspec].mode = S_IFLNK;
			break;
		case 's':
			spec_arr[nspec].mode = S_IFSOCK;
			break;
		case '-':
			spec_arr[nspec].mode = S_IFREG;
			break;
		default:
			myprintf("%s:  line %d has invalid file type %s\n", path, lineno, type); 
			return 0;
		}
		
	skip_type:
		if (strcmp(context, "<<none>>")) {
			if (context_translations) {
				if (raw_to_trans_context(context,
				                    &spec_arr[nspec].context)) {
					myprintf("%s: line %u has invalid "
					         "context %s\n",
					         path, lineno, context);
					return 0;
				}
				free(context);
				context = spec_arr[nspec].context;
			} else {
				if (STRIP_LEVEL(&context, mls_enabled))
					return -1;
			}

			if (myinvalidcon(path, lineno, context))
				return 0;
		}

		spec_arr[nspec].context = context;
		
		/* Determine if specification has 
		 * any meta characters in the RE */
		spec_hasMetaChars(&spec_arr[nspec]);
	}
	
	nspec++;
	if (pass == 0) {
		free(regex);
		if (type)
			free(type);
		free(context);
	}
	return 0;
}

int matchpathcon_init(const char *path)
{
	FILE *fp;
	FILE *localfp = NULL;
	FILE *homedirfp = NULL;
	char local_path[PATH_MAX + 1];
	char homedir_path[PATH_MAX + 1];
	char *line_buf = NULL;
	size_t line_len = 0;
	unsigned int lineno, pass, i, j, maxnspec;
	spec_t *spec_copy=NULL;
	int status=-1;
	int mls_enabled=is_selinux_mls_enabled();

	/* Open the specification file. */
	if (!path)
		path = selinux_file_context_path();
	if ((fp = fopen(path, "r")) == NULL)
		return -1;
	__fsetlocking(fp, FSETLOCKING_BYCALLER);

	if ((myflags & MATCHPATHCON_BASEONLY) == 0) {
		snprintf(homedir_path, sizeof(homedir_path), "%s.homedirs", path);
		homedirfp = fopen(homedir_path, "r");
		if (homedirfp != NULL)
			__fsetlocking(homedirfp, FSETLOCKING_BYCALLER);

		snprintf(local_path, sizeof(local_path), "%s.local", path);
		localfp = fopen(local_path, "r");
		if (localfp != NULL)
			__fsetlocking(localfp, FSETLOCKING_BYCALLER);
	}

	/* 
	 * Perform two passes over the specification file.
	 * The first pass counts the number of specifications and
	 * performs simple validation of the input.  At the end
	 * of the first pass, the spec array is allocated.
	 * The second pass performs detailed validation of the input
	 * and fills in the spec array.
	 */
	maxnspec = UINT_MAX / sizeof(spec_t);
	for (pass = 0; pass < 2; pass++) {
		lineno = 0;
		nspec = 0;
		while (getline(&line_buf, &line_len, fp) > 0 && nspec < maxnspec) {
			if (process_line(path, line_buf, pass, ++lineno, mls_enabled) != 0)
				goto finish;
		}
		lineno = 0;
		if (homedirfp) 
			while (getline(&line_buf, &line_len, homedirfp) > 0 && nspec < maxnspec) {
				if (process_line(homedir_path, line_buf, pass, ++lineno, mls_enabled) != 0)
					goto finish;
			}

		lineno = 0;
		if (localfp) 
			while (getline(&line_buf, &line_len, localfp) > 0 && nspec < maxnspec) {
				if (process_line(local_path, line_buf, pass, ++lineno, mls_enabled) != 0)
					goto finish;
			}

		if (pass == 0) {
			if (nspec == 0) {
				status = 0;
				goto finish;
			}
			if ((spec_arr = malloc(sizeof(spec_t) * nspec)) ==
			    NULL)
				goto finish;
			memset(spec_arr, '\0', sizeof(spec_t) * nspec);
			maxnspec = nspec;
			rewind(fp);
			if (homedirfp) rewind(homedirfp);
			if (localfp) rewind(localfp);
		}
	}
	free(line_buf);

	/* Move exact pathname specifications to the end. */
	spec_copy = malloc(sizeof(spec_t) * nspec);
	if (!spec_copy)
		goto finish;
	j = 0;
	for (i = 0; i < nspec; i++) {
		if (spec_arr[i].hasMetaChars)
			memcpy(&spec_copy[j++], &spec_arr[i], sizeof(spec_t));
	}
	for (i = 0; i < nspec; i++) {
		if (!spec_arr[i].hasMetaChars)
			memcpy(&spec_copy[j++], &spec_arr[i], sizeof(spec_t));
	}
	free(spec_arr);
	spec_arr = spec_copy;

	nodups_specs(path);

	status = 0;
 finish:
	fclose(fp);
	if (spec_arr != spec_copy) free(spec_arr);
	if (homedirfp) fclose(homedirfp);
	if (localfp) fclose(localfp);
	return status;
}
hidden_def(matchpathcon_init)

static int matchpathcon_common(const char *name, 
			       mode_t mode)
{
	int i, ret, file_stem;
	const char *buf = name;

	if (!nspec) {
		ret = matchpathcon_init(NULL);
		if (ret < 0)
			return ret;
		if (!nspec) {
			errno = ENOENT;
			return -1;
		}
	}

	file_stem = find_stem_from_file(&buf);

	mode &= S_IFMT;

	/* 
	 * Check for matching specifications in reverse order, so that
	 * the last matching specification is used.
	 */
	for (i = nspec - 1; i >= 0; i--)
	{
		/* if the spec in question matches no stem or has the same
		 * stem as the file AND if the spec in question has no mode
		 * specified or if the mode matches the file mode then we do
		 * a regex check	*/
		if( (spec_arr[i].stem_id == -1 || spec_arr[i].stem_id == file_stem)
		  && (!mode || !spec_arr[i].mode || ( (mode & S_IFMT) == spec_arr[i].mode ) ) )
		{
			if(spec_arr[i].stem_id == -1)
				ret = regexec(&spec_arr[i].regex, name, 0, NULL, 0);
			else
				ret = regexec(&spec_arr[i].regex, buf, 0, NULL, 0);
			if (ret == 0)
				break;

			if (ret == REG_NOMATCH)
				continue;
			/* else it's an error */
			return -1;
		}
	}

	if (i < 0) {
		/* No matching specification. */
		errno = ENOENT;
		return -1;
	}

	spec_arr[i].matches++;

	return i;

}

int matchpathcon(const char *name, 
		 mode_t mode,
		 security_context_t *con)
{
	int i = matchpathcon_common(name, mode);

	if (i < 0)
		return -1;

	if (strcmp(spec_arr[i].context, "<<none>>") == 0) {
		errno = ENOENT;
		return -1;
	}

	*con = strdup(spec_arr[i].context);
	if (!(*con))
		return -1;

	return 0;
}

int matchpathcon_index(const char *name, 
		       mode_t mode,
		       security_context_t *con)
{
	int i = matchpathcon_common(name, mode);

	if (i < 0)
		return -1;

	*con = strdup(spec_arr[i].context);
	if (!(*con))
		return -1;

	return i;
}

void matchpathcon_checkmatches(char *str)
{
	unsigned int i;
	for (i = 0; i < nspec; i++) {
		if (spec_arr[i].matches == 0) {
			if (spec_arr[i].type_str) {
				myprintf
					("%s:  Warning!  No matches for (%s, %s, %s)\n",
					 str, spec_arr[i].regex_str,
					 spec_arr[i].type_str, spec_arr[i].context);
			} else {
				myprintf
					("%s:  Warning!  No matches for (%s, %s)\n",
					 str, spec_arr[i].regex_str,
					 spec_arr[i].context);
			}
		}
	}
}
