#include <stdio.h>
#include <string.h>
#include <ctype.h>
#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <limits.h>
#include <unistd.h>
#include "selinux_internal.h"
#include "get_default_type_internal.h"

#define SELINUXDIR "/etc/selinux/"
#define SELINUXCONFIG SELINUXDIR "config"
#define SELINUXDEFAULT "targeted"
#define SELINUXTYPETAG "SELINUXTYPE="
#define SELINUXTAG "SELINUX="
#define SETLOCALDEFS "SETLOCALDEFS="
#define REQUIRESEUSERS "REQUIRESEUSERS="

/* Indices for file paths arrays. */
#define BINPOLICY         0
#define CONTEXTS_DIR      1    
#define FILE_CONTEXTS     2
#define DEFAULT_CONTEXTS  3
#define USER_CONTEXTS     4
#define FAILSAFE_CONTEXT  5
#define DEFAULT_TYPE      6
#define BOOLEANS          7
#define MEDIA_CONTEXTS    8
#define REMOVABLE_CONTEXT 9
#define CUSTOMIZABLE_TYPES    10
#define USERS_DIR         11
#define SEUSERS           12
#define NEL               13

/* New layout is relative to SELINUXDIR/policytype. */
static char *file_paths[NEL];
#define L1(l) L2(l)
#define L2(l)str##l
static const union file_path_suffixes_data {
  struct {
#define S_(n, s) char L1(__LINE__)[sizeof(s)];
#include "file_path_suffixes.h"
#undef S_
  };
  char str[0];
} file_path_suffixes_data =
{
  {
#define S_(n, s) s,
#include "file_path_suffixes.h"
#undef S_
  }
};
static const uint16_t file_path_suffixes_idx[NEL] =
{
#define S_(n, s) [n] = offsetof(union file_path_suffixes_data, L1(__LINE__)),
#include "file_path_suffixes.h"
#undef S_
};

/* Old layout had fixed locations. */
#define SECURITYCONFIG "/etc/sysconfig/selinux"
#define SECURITYDIR "/etc/security"
static const union compat_file_path_data {
  struct {
#define S_(n, s) char L1(__LINE__)[sizeof(s)];
#include "compat_file_path.h"
#undef S_
  };
  char str[0];
} compat_file_path_data =
{
  {
#define S_(n, s) s,
#include "compat_file_path.h"
#undef S_
  }
};
static const uint16_t compat_file_path_idx[NEL] =
{
#define S_(n, s) [n] = offsetof(union compat_file_path_data, L1(__LINE__)),
#include "compat_file_path.h"
#undef S_
};
#undef L1
#undef L2

static int use_compat_file_path;

int selinux_getenforcemode(int *enforce) {
  int ret=-1;
  FILE *cfg = fopen(SELINUXCONFIG,"r");
  char buf[4097];
  int len=sizeof(SELINUXTAG)-1;
  if (!cfg) {
    cfg = fopen(SECURITYCONFIG,"r");
  }
  if (cfg) {
    while (fgets_unlocked(buf, 4096, cfg)) {
      if (strncmp(buf,SELINUXTAG,len))
	continue;
      if (!strncasecmp(buf+len,"enforcing",sizeof("enforcing")-1)) {
	*enforce = 1;
	ret=0;
	break;
      } else if (!strncasecmp(buf+len,"permissive",sizeof("permissive")-1)) {
	*enforce = 0;
	ret=0;
	break;
      } else if (!strncasecmp(buf+len,"disabled",sizeof("disabled")-1)) {
	*enforce = -1;
	ret=0;
	break;
      }
    }
    fclose(cfg);
  }
  return ret;
}
hidden_def(selinux_getenforcemode)

static char *selinux_policyroot = NULL;

static void init_selinux_config(void) __attribute__ ((constructor));

static void init_selinux_config(void)
{
  int i, *intptr;
  size_t rootlen, len;
  char *line_buf = NULL, *buf_p, *value;
  FILE *fp;

  if (selinux_policyroot) return;
  if (access(SELINUXDIR, F_OK) != 0) {
	  selinux_policyroot = SECURITYDIR;
	  use_compat_file_path = 1;
	  return;
  }

  fp = fopen(SELINUXCONFIG,"r");
  if (fp) {
	  while (getline(&line_buf, &len, fp) > 0) {
		  len = strlen(line_buf); /* reset in case of embedded NUL */
		  if (line_buf[len - 1] == '\n')
			  line_buf[len - 1] = 0;
		  buf_p = line_buf;
		  while (isspace(*buf_p))
			  buf_p++;
		  if (*buf_p == '#' || *buf_p == 0)
			  continue;

		  if (!strncasecmp(buf_p, SELINUXTYPETAG, 
				   sizeof(SELINUXTYPETAG)-1)) {
			  char *type, *end;
			  type = buf_p+sizeof(SELINUXTYPETAG)-1;
			  end  = type + strlen(type)-1;
			  while ((end > type) && 
				 (isspace(*end) || iscntrl(*end))) {
				  *end = 0;
				  end--;
			  }
			  rootlen = sizeof(SELINUXDIR) + strlen(type);
			  selinux_policyroot = malloc(rootlen);
			  if (!selinux_policyroot)
				  return;
			  snprintf(selinux_policyroot, rootlen, "%s%s", 
				   SELINUXDIR, type);
			  continue;
		  } else if (!strncmp(buf_p, SETLOCALDEFS, 
				      sizeof(SETLOCALDEFS)-1)) {
			  value = buf_p + sizeof(SETLOCALDEFS)-1;
			  intptr = &load_setlocaldefs;
		  } else if (!strncmp(buf_p, REQUIRESEUSERS, 
				      sizeof(REQUIRESEUSERS)-1)) {
			  value = buf_p + sizeof(REQUIRESEUSERS)-1;
			  intptr = &require_seusers;
		  } else {
			  continue;
		  }

		  if (isdigit(*value)) 
			  *intptr = atoi(value);
		  else if (strncasecmp(value, "true", sizeof("true")-1))
			  *intptr = 1;
		  else if (strncasecmp(value, "false", sizeof("false")-1))
			  *intptr = 0;
	  }
	  free(line_buf);
	  fclose(fp);
  }

  for (i = 0; i < NEL; i++) {
	  len = rootlen + strlen(file_path_suffixes_data.str
				 + file_path_suffixes_idx[i])+1;
	  file_paths[i] = malloc(len);
	  if (!file_paths[i])
		  return;
	  snprintf(file_paths[i], len, "%s%s", selinux_policyroot,
		   file_path_suffixes_data.str + file_path_suffixes_idx[i]);
  }
  use_compat_file_path = 0;
}

static void fini_selinux_policyroot(void) __attribute__ ((destructor));

static void fini_selinux_policyroot(void)
{
  int i;
  if (use_compat_file_path) {
	  selinux_policyroot = NULL;
	  return;
  }
  free(selinux_policyroot);
  selinux_policyroot = NULL;
  for (i = 0; i < NEL; i++) {
	  free(file_paths[i]);
	  file_paths[i] = NULL;
  }  
}

static const char *get_path(int idx)
{
  if (!use_compat_file_path)
    return file_paths[idx];

  return compat_file_path_data.str + compat_file_path_idx[idx];
}

const char *selinux_default_type_path() 
{
  return get_path(DEFAULT_TYPE);
}
hidden_def(selinux_default_type_path)

const char *selinux_policy_root() {
	return selinux_policyroot;
}

const char *selinux_default_context_path() {
  return get_path(DEFAULT_CONTEXTS);
}
hidden_def(selinux_default_context_path)

const char *selinux_failsafe_context_path() {
  return get_path(FAILSAFE_CONTEXT);
}
hidden_def(selinux_failsafe_context_path)

const char *selinux_removable_context_path() {
  return get_path(REMOVABLE_CONTEXT);
}
hidden_def(selinux_removable_context_path)

const char *selinux_binary_policy_path() {
  return get_path(BINPOLICY);
}
hidden_def(selinux_binary_policy_path)

const char *selinux_file_context_path() {
  return get_path(FILE_CONTEXTS);
}
hidden_def(selinux_file_context_path)

const char *selinux_media_context_path() {
  return get_path(MEDIA_CONTEXTS);
}
hidden_def(selinux_media_context_path)

const char *selinux_customizable_types_path() {
  return get_path(CUSTOMIZABLE_TYPES);
}
hidden_def(selinux_customizable_types_path)

const char *selinux_contexts_path() {
  return get_path(CONTEXTS_DIR);
}

const char *selinux_user_contexts_path() {
  return get_path(USER_CONTEXTS);
}
hidden_def(selinux_user_contexts_path)

const char *selinux_booleans_path() {
  return get_path(BOOLEANS);
}
hidden_def(selinux_booleans_path)

const char *selinux_users_path() {
  return get_path(USERS_DIR);
}
const char *selinux_usersconf_path() {
  return get_path(SEUSERS);
}

hidden_def(selinux_users_path)
hidden_def(selinux_usersconf_path)

