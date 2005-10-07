#include "selinux_internal.h"
#include <string.h>

int (*lib_trans_to_raw_context)(char *trans, char **rawp) hidden;
int (*lib_raw_to_trans_context)(char *raw, char **transp) hidden;

int hidden trans_to_raw_context(char *trans, char **rawp)
{
	*rawp = NULL;
	if (!trans)
		return 0;

	if (trans && lib_trans_to_raw_context(trans, rawp))
		*rawp = strdup(trans);

	return *rawp ? 0 : -1;
}

int selinux_trans_to_raw_context(security_context_t trans, 
				 security_context_t *rawp)
{
	if (context_translations)
		return trans_to_raw_context(trans, rawp);

	if (!trans) {
		*rawp = NULL;
		return 0;
	}

	*rawp = strdup(trans);
	return *rawp ? 0 : -1;
}

int hidden raw_to_trans_context(char *raw, char **transp) 
{
	*transp = NULL;
	if (!raw)
		return 0;

	if (raw && lib_raw_to_trans_context(raw, transp))
		*transp = strdup(raw);

	return *transp ? 0 : -1;
}

int selinux_raw_to_trans_context(security_context_t raw, 
				 security_context_t *transp)
{
	if (context_translations)
		return raw_to_trans_context(raw, transp);

	if (!raw) {
		*transp = NULL;
		return 0;
	}

	*transp = strdup(raw);
	return *transp ? 0 : -1;
}
