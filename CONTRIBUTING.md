# ncdfchecker: How to Contribute


## Raising Bug Reports or Feature Requests

Please raise issues to capture bugs or feature requests - or feel free
to contact us directly and discuss things if you have our contact details.


## Contributing Code or Reviewing

We really appreciate code or review contributions!

Code contributions are made by raising pull requests against the master
branch of https://github.com/metosfc/ncdfchecker/. If you are a new
contributor, your pull request must include adding your details to the list of
contributors under the [Code Contributors](#code-contributors) part of this
page.

Reviewers of the pull requests must check this has been done before the pull
request is merged into master.

Prior to requesting review of a pull request, please ensure that tests are
fully working and have been added to as necessary, and that code is pep8
compliant.

## Development Principles

Some useful principles to follow when you want to make a code contribution:

* When contributing to this codebase please use the forking workflow 
  https://www.atlassian.com/git/tutorials/comparing-workflows/forking-workflow
  to carry out your development work in your own fork and then raise pull requests
  against the main repository when you are ready.

* When adding to/extending/altering the code remember that the tool is intended
  to be driven by the contents of a provided config file. This means that any
  desired behaviour should be captured in the form of a config item rather than
  specifically catering for it in code.

* Double check if an existing config item covers what you need or if it is very
  close to what you want. This may save you time and effort!

## Code Contributors

The following people have contributed to this code under the terms of
the Contributor Licence Agreement and Certificate of Origin detailed
below:

* Andrew Clark (Met Office, UK)
* Nicola Martin (Met Office, UK)
* Craig MacLachlan (Met Office, UK)
* Jamie Kettleborough (Met Office, UK)
* Philip Davis (Met Office, UK)

(All contributors on GitHub are identifiable with email addresses in the
version control logs or otherwise.)


## Contributor Licence Agreement and Certificate of Origin

By making a contribution to this project, I certify that:

(a) The contribution was created in whole or in part by me and I have
    the right to submit it, either on my behalf or on behalf of my
    employer, under the terms and conditions as described by this file;
    or

(b) The contribution is based upon previous work that, to the best of
    my knowledge, is covered under an appropriate licence and I have
    the right or permission from the copyright owner under that licence
    to submit that work with modifications, whether created in whole or
    in part by me, under the terms and conditions as described by
    this file; or

(c) The contribution was provided directly to me by some other person
    who certified (a) or (b) and I have not modified it.

(d) I understand and agree that this project and the contribution
    are public and that a record of the contribution (including my
    name and email address) is maintained for the full term of the copyright
    and may be redistributed consistent with this project or the licence(s)
    involved.

(e) I, or my employer, grant to the UK Met Office and all recipients of
    this software a perpetual, worldwide, non-exclusive, no-charge,
    royalty-free, irrevocable copyright licence to reproduce, modify,
    prepare derivative works of, publicly display, publicly perform,
    sub-licence, and distribute this contribution and such modifications
    and derivative works consistent with this project or the licence(s)
    involved or other appropriate open source licence(s) specified by
    the project and approved by the
    [Open Source Initiative (OSI)](http://www.opensource.org/).

(f) If I become aware of anything that would make any of the above
    inaccurate, in any way, I will let the UK Met Office know as soon as
    I become aware.

(This Contributor Licence Agreement and Certificate of Origin is
derived almost entirely from the IMPROVER version
(https://github.com/metoppv/improver/), which was inspired by the Certificate
of Origin used by Enyo and the Linux Kernel.)
