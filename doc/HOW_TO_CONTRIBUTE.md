# Contributing

If you are interested in working on Reference Policy, feel free to
contact the developers on the Reference Policy mailing
list. To join the mail list, send a plaintext email to <majordomo@vger.kernel.org>
containing "subscribe selinux-refpolicy" in the body. All public
development related discussion happens on this mailing list. The IRC
channel, \#selinux on irc.libera.chat, is also appropriate for
development discussions.

Reference Policy changes should be submitted by pull requests on GitHub or by sending patches to
the mail list. Pull requests on GitHub are preferred. Where feasible, please
include denial messages that are addressed by the patches.

## Developers Certificate of Origin

Each patch is required to include a Signed-off-by certifying that you wrote the patch or are
otherwise authorized to contribute it as open source. You must use your real name (sorry, no
pseudonyms or anonymous contributions.)

<https://developercertificate.org>

```text
Developer Certificate of Origin
Version 1.1

Copyright (C) 2004, 2006 The Linux Foundation and its contributors.
1 Letterman Drive
Suite D4700
San Francisco, CA, 94129

Everyone is permitted to copy and distribute verbatim copies of this
license document, but changing it is not allowed.


Developer's Certificate of Origin 1.1

By making a contribution to this project, I certify that:

(a) The contribution was created in whole or in part by me and I
    have the right to submit it under the open source license
    indicated in the file; or

(b) The contribution is based upon previous work that, to the best
    of my knowledge, is covered under an appropriate open source
    license and I have the right under that license to submit that
    work with modifications, whether created in whole or in part
    by me, under the same open source license (unless I am
    permitted to submit under a different license), as indicated
    in the file; or

(c) The contribution was provided directly to me by some other
    person who certified (a), (b) or (c) and I have not modified
    it.

(d) I understand and agree that this project and the contribution
    are public and that a record of the contribution (including all
    personal information I submit with it, including my sign-off) is
    maintained indefinitely and may be redistributed consistent with
    this project or the open source license(s) involved.
```

## Patches via Mail List

When submitting patches, there are a few things to keep in mind:

- It is strongly preferred (but not required) that patches be created
  by "git format-patch -n -s" **and** sent via "git send-email". This
  will ensure the patch can be directly imported into the repository,
  if accepted. Please ensure that the [name and email
  address](http://github.com/guides/tell-git-your-user-name-and-email-address)
  are correct on your patches before committing to your local repo.
- It is a common convention to prefix your subject line with [PATCH].
  This lets people easily distinguish patches from other e-mail
  discussions. Use of additional markers after PATCH and the closing
  bracket to mark the nature of the patch is also encouraged. E.g.
  [PATCH/RFC] is often used when the patch is not ready to be applied
  but it is for discussion, [PATCH v2], [PATCH v3] etc. are often seen
  when you are sending an update to what you have previously sent.

## How To Create A Patch Set for the Mail List

- A patch should make one logical change. Don't make multiple,
  disjoint changes to different modules in a single patch.
- A given patch should not break anything, even if later patches fix
  the problems that it causes. The tree should still compile after
  each patch is applied. (This makes "git bisect" work correctly.)
- Include a Signed-off-by: Your Name <youremail@domain.com> in your
  commit messages.  "git commit -s" is one way to easily add it.
- Patches should be relative to HEAD of the git master branch.
- Make patches relative to the top of the policy source tree (the
  directory where the Makefile and build.conf are). This is
  automatically done when using git format-patch.
- A summary email that describes the set should also be sent for patch
  sets that consist of many patches. Typically this is patch 0, e.g.
  [PATCH 0/4]
- A link to a git repo from which the set can be pulled is preferred
  if the patch set is very large.
