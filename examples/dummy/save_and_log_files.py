#!/usr/bin/env python3

"""
Example on how to save ExpFiles, how to log ExpFiles and how to log references
to any files, even those not tracked by dbx.
"""

import dbxlogger as dbx

def main():

    # RefFile and logger demo, no exps involved yet
    ref = dbx.RefFile("./readme.md")
    print("readme.md sha-256: %s" % ref.sha256)

    log = dbx.StdoutLogger()
    log("saved-readme", {"my-ref": ref})

    # let's create an Exp and an ExpFile
    repo = dbx.get_repo("./output") # we need a repo to create an experiment
    exp = dbx.Exp(repo, kind="dummy", name="files-example")
    exp.save() # we need to create the exp in the repo

    # let's create an expfile in which we write "hello world"
    with exp.file("hello.txt", "w") as f:
        print("hello world", file=f)

    # if we want to also log a reference to the file
    log = exp.logger()

    expfile = exp.file("second_file.txt", "w")
    with expfile as f:
        print("second file example", file=f)

    # always log after finished writing, since we compute a hash of the file
    log("saved", {"my-file": expfile})


if __name__ == "__main__":
    main()
