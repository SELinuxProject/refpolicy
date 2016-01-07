/* Copyright 2005,2013 Tresys Technology
 *
 * Some parts of this came from matchpathcon.c in libselinux
 */

/* PURPOSE OF THIS PROGRAM
 * The original setfiles sorting algorithm did not take into
 * account regular expression specificity. With the current
 * strict and targeted policies this is not an issue because
 * the file contexts are partially hand sorted and concatenated
 * in the right order so that the matches are generally correct.
 * The way reference policy and loadable policy modules handle
 * file contexts makes them come out in an unpredictable order
 * and therefore setfiles (or this standalone tool) need to sort
 * the regular expressions in a deterministic and stable way.
 */

#define BUF_SIZE 4096;
#define _GNU_SOURCE

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

typedef unsigned char bool_t;

/* file_context_node
 * A node used in a linked list of file contexts.c
 * Each node contains the regular expression, the type and
 *  the context, as well as information about the regular
 *  expression. The regular expression data (meta, stem_len
 *  and str_len) can be filled in by using the fc_fill_data
 *  function after the regular expression has been loaded.
 * next points to the next node in the linked list.
 */
typedef struct file_context_node {
	char *path;
	char *file_type;
	char *context;
	bool_t meta;
	int stem_len;
	int str_len;
	struct file_context_node *next;
} file_context_node_t;

void file_context_node_destroy(file_context_node_t *x)
{
	free(x->path);
	free(x->file_type);
	free(x->context);
}



/* file_context_bucket
 * A node used in a linked list of buckets that contain
 *  file_context_node's.
 * Each node contains a pointer to a file_context_node which
 *  is the header of its linked list. This linked list is the
 *  content of this bucket.
 * next points to the next bucket in the linked list.
 */
typedef struct file_context_bucket {
	file_context_node_t *data;
	struct file_context_bucket *next;
} file_context_bucket_t;



/* fc_compare
 * Compares two file contexts' regular expressions and returns:
 *    -1 if a is less specific than b
 *     0 if a and be are equally specific
 *     1 if a is more specific than b
 * The comparison is based on the following statements,
 *  in order from most important to least important, given a and b:
 *     If a is a regular expression and b is not,
 *      -> a is less specific than b.
 *     If a's stem length is shorter than b's stem length,
 *      -> a is less specific than b.
 *     If a's string length is shorter than b's string length,
 *      -> a is less specific than b.
 *     If a does not have a specified type and b does,
 *      -> a is less specific than b.
 */
int fc_compare(file_context_node_t *a, file_context_node_t *b)
{
	/* Check to see if either a or b have meta characters
	 *  and the other doesn't. */
	if (a->meta && !b->meta)
		return -1;
	if (b->meta && !a->meta)
		return 1;

	/* Check to see if either a or b have a shorter stem
	 *  length than the other. */
	if (a->stem_len < b->stem_len)
		return -1;
	if (b->stem_len < a->stem_len)
		return 1;

	/* Check to see if either a or b have a shorter string
	 *  length than the other. */
	if (a->str_len < b->str_len)
		return -1;
	if (b->str_len < a->str_len)
		return 1;

	/* Check to see if either a or b has a specified type
	 *  and the other doesn't. */
	if (!a->file_type && b->file_type)
		return -1;
	if (!b->file_type && a->file_type)
		return 1;

	/* If none of the above conditions were satisfied,
	 * then a and b are equally specific. */
	return 0;
}



/* fc_merge
 * Merges two sorted file context linked lists into one
 *  sorted one.
 * Pass two lists a and b, and after the completion of fc_merge,
 *  the final list is contained in a, and b is empty.
 */
file_context_node_t *fc_merge(file_context_node_t *a,
				   file_context_node_t *b)
{
	file_context_node_t *a_current;
	file_context_node_t *b_current;
	file_context_node_t *temp;
	file_context_node_t *jumpto;



	/* If a is a empty list, and b is not,
	 *  set a as b and proceed to the end. */
	if (!a && b)
		a = b;
	/* If b is an empty list, leave a as it is. */
	else if (!b) {
	} else {
		/* Make it so the list a has the lesser
		 *  first element always. */
		if (fc_compare(a, b) == 1) {
			temp = a;
			a = b;
			b = temp;
		}
		a_current = a;
		b_current = b;

		/* Merge by inserting b's nodes in between a's nodes. */
		while (a_current->next && b_current) {
			jumpto = a_current->next;

			/* Insert b's nodes in between the current a node
			 *  and the next a node.*/
			while (b_current && a_current->next &&
			       fc_compare(a_current->next,
					  b_current) != -1) {


				temp = a_current->next;
				a_current->next = b_current;
				b_current = b_current->next;
				a_current->next->next = temp;
				a_current = a_current->next;
			}

			/* Skip all the inserted node from b to the
			 *  next node in the original a. */
			a_current = jumpto;
		}


		/* if there is anything left in b to be inserted,
		   put it on the end */
		if (b_current) {
			a_current->next = b_current;
		}
	}

	return a;
}



/* fc_merge_sort
 * Sorts file contexts from least specific to more specific.
 * The bucket linked list is passed and after the completion
 *  of the fc_merge_sort function, there is only one bucket
 *  (pointed to by master) that contains a linked list
 *  of all the file contexts, in sorted order.
 * Explanation of the algorithm:
 *  The algorithm implemented in fc_merge_sort is an iterative
 *   implementation of merge sort.
 *  At first, each bucket has a linked list of file contexts
 *   that are 1 element each.
 *  Each pass, each odd numbered bucket is merged into the bucket
 *   before it. This halves the number of buckets each pass.
 *  It will continue passing over the buckets (as described above)
 *   until there is only  one bucket left, containing the list of
 *   file contexts, sorted.
 */
void fc_merge_sort(file_context_bucket_t *master)
{


	file_context_bucket_t *current;
	file_context_bucket_t *temp;

	/* Loop until master is the only bucket left
	 * so that this will stop when master contains
	 * the sorted list. */
	while (master->next) {
		current = master;

		/* This loop merges buckets two-by-two. */
		while (current) {

			if (current->next) {

				current->data =
				    fc_merge(current->data,
					     current->next->data);



				temp = current->next;
				current->next = current->next->next;

				free(temp);

			}


			current = current->next;
		}
	}


}



/* fc_fill_data
 * This processes a regular expression in a file context
 *  and sets the data held in file_context_node, namely
 *  meta, str_len and stem_len.
 * The following changes are made to fc_node after the
 *  the completion of the function:
 *     fc_node->meta =		1 if path has a meta character, 0 if not.
 *     fc_node->str_len =	The string length of the entire path
 *     fc_node->stem_len = 	The number of characters up until
 *				 the first meta character.
 */
void fc_fill_data(file_context_node_t *fc_node)
{
	int c = 0;

	fc_node->meta = 0;
	fc_node->stem_len = 0;
	fc_node->str_len = 0;

	/* Process until the string termination character
	 *  has been reached.
	 * Note: this while loop has been adapted from
	 *  spec_hasMetaChars in matchpathcon.c from
	 *  libselinux-1.22. */
	while (fc_node->path[c] != '\0') {
		switch (fc_node->path[c]) {
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
			/* If a meta character is found,
			 *  set meta to one */
			fc_node->meta = 1;
			break;
		case '\\':
			/* If a escape character is found,
			 *  skip the next character. */
			c++;
		default:
			/* If no meta character has been found yet,
			 *  add one to the stem length. */
			if (!fc_node->meta)
				fc_node->stem_len++;
			break;
		}

		fc_node->str_len++;
		c++;
	}
}

/* main
 * This program takes in two arguments, the input filename and the
 *  output filename. The input file should be syntactically correct.
 * Overall what is done in the main is read in the file and store each
 *  line of code, sort it, then output it to the output file.
 */
int main(int argc, char *argv[])
{
	int lines;
	size_t start, finish, regex_len, context_len;
	size_t line_len, buf_len, i, j;
	char *input_name, *output_name, *line_buf;

	file_context_node_t *temp;
	file_context_node_t *head;
	file_context_node_t *current;
	file_context_bucket_t *master;
	file_context_bucket_t *bcurrent;

	FILE *in_file, *out_file;


	/* Check for the correct number of command line arguments. */
	if (argc < 2 || argc > 3) {
		fprintf(stderr, "Usage: %s <infile> [<outfile>]\n",argv[0]);
		return 1;
	}

	input_name = argv[1];
	output_name = (argc >= 3) ? argv[2] : NULL;

	i = j = lines = 0;

	/* Open the input file. */
	if (!(in_file = fopen(input_name, "r"))) {
		fprintf(stderr, "Error: failure opening input file for read.\n");
		return 1;
	}

	/* Initialize the head of the linked list. */
	head = current = (file_context_node_t*)malloc(sizeof(file_context_node_t));
	head->next = NULL;

	/* Parse the file into a file_context linked list. */
	line_buf = NULL;

	while ( getline(&line_buf, &buf_len, in_file) != -1 ){
		line_len = strlen(line_buf);
		if( line_len == 0 || line_len == 1)
			continue;
		/* Get rid of whitespace from the front of the line. */
		for (i = 0; i < line_len; i++) {
			if (!isspace(line_buf[i]))
				break;
		}


		if (i >= line_len)
			continue;
		/* Check if the line isn't empty and isn't a comment */
		if (line_buf[i] == '#')
			continue;

		/* We have a valid line - allocate a new node. */
		temp = (file_context_node_t *)malloc(sizeof(file_context_node_t));
		if (!temp) {
			fprintf(stderr, "Error: failure allocating memory.\n");
			return 1;
		}
		temp->next = NULL;
		memset(temp, 0, sizeof(file_context_node_t));

		/* Parse out the regular expression from the line. */
		start = i;


		while (i < line_len && (!isspace(line_buf[i])))
			i++;
		finish = i;


		regex_len = finish - start;

		if (regex_len == 0) {
			file_context_node_destroy(temp);
			free(temp);


			continue;
		}

		temp->path = (char*)strndup(&line_buf[start], regex_len);
		if (!temp->path) {
			file_context_node_destroy(temp);
			free(temp);
			fprintf(stderr, "Error: failure allocating memory.\n");
			return 1;
		}

		/* Get rid of whitespace after the regular expression. */
		for (; i < line_len; i++) {

			if (!isspace(line_buf[i]))
				break;
		}

		if (i == line_len) {
			file_context_node_destroy(temp);
			free(temp);
			continue;
		}

		/* Parse out the type from the line (if it
			*  is there). */
		if (line_buf[i] == '-') {
			temp->file_type = (char *)malloc(sizeof(char) * 3);
			if (!(temp->file_type)) {
				fprintf(stderr, "Error: failure allocating memory.\n");
				return 1;
			}

			if( i + 2 >= line_len ) {
				file_context_node_destroy(temp);
				free(temp);

				continue;
			}

			/* Fill the type into the array. */
			temp->file_type[0] = line_buf[i];
			temp->file_type[1] = line_buf[i + 1];
			i += 2;
			temp->file_type[2] = 0;

			/* Get rid of whitespace after the type. */
			for (; i < line_len; i++) {
				if (!isspace(line_buf[i]))
					break;
			}

			if (i == line_len) {

				file_context_node_destroy(temp);
				free(temp);
				continue;
			}
		}

		/* Parse out the context from the line. */
		start = i;
		while (i < line_len && (!isspace(line_buf[i])))
			i++;
		finish = i;

		context_len = finish - start;

		temp->context = (char*)strndup(&line_buf[start], context_len);
		if (!temp->context) {
			file_context_node_destroy(temp);
			free(temp);
			fprintf(stderr, "Error: failure allocating memory.\n");
			return 1;
		}

		/* Set all the data about the regular
			*  expression. */
		fc_fill_data(temp);

		/* Link this line of code at the end of
			*  the linked list. */
		current->next = temp;
		current = current->next;
		lines++;


		free(line_buf);
		line_buf = NULL;
	}
	fclose(in_file);

	/* Create the bucket linked list from the earlier linked list. */
	current = head->next;
	bcurrent = master =
	    (file_context_bucket_t *)
	    malloc(sizeof(file_context_bucket_t));
	bcurrent->next = NULL;
	bcurrent->data = NULL;

	/* Go until all the nodes have been put in individual buckets. */
	while (current) {
		/* Copy over the file context line into the bucket. */
		bcurrent->data = current;
		current = current->next;

		/* Detach the node in the bucket from the old list. */
		bcurrent->data->next = NULL;

		/* If there should be another bucket, put one at the end. */
		if (current) {
			bcurrent->next =
			    (file_context_bucket_t *)
			    malloc(sizeof(file_context_bucket_t));
			if (!(bcurrent->next)) {
				printf
				    ("Error: failure allocating memory.\n");
				return -1;
			}

			/* Make sure the new bucket thinks it's the end of the
			 *  list. */
			bcurrent->next->next = NULL;

			bcurrent = bcurrent->next;
		}

	}

	/* Sort the bucket list. */
	fc_merge_sort(master);

	/* Open the output file. */
	if (output_name) {
		if (!(out_file = fopen(output_name, "w"))) {
			printf("Error: failure opening output file for write.\n");
			return -1;
		}
	} else {
		out_file = stdout;
	}

	/* Output the sorted file_context linked list to the output file. */
	current = master->data;
	while (current) {
		/* Output the path. */
		fprintf(out_file, "%s\t\t", current->path);

		/* Output the type, if there is one. */
		if (current->file_type) {
			fprintf(out_file, "%s\t", current->file_type);
		}

		/* Output the context. */
		fprintf(out_file, "%s\n", current->context);

		/* Remove the node. */
		temp = current;
		current = current->next;

		file_context_node_destroy(temp);
		free(temp);

	}
	free(master);

	if (output_name) {
		fclose(out_file);
	}

	return 0;
}
