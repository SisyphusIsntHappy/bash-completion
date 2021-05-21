import pytest
import os
import tempfile
import re

from conftest import assert_bash_exec


@pytest.mark.bashcomp(cmd=None, temp_cwd=True)
class TestUnitQuoteReadline:
    def test_exec(self, bash):
        assert_bash_exec(bash, "quote_readline '' >/dev/null")

    def test_env_non_pollution(self, bash):
        """Test environment non-pollution, detected at teardown."""
        assert_bash_exec(
            bash, "foo() { quote_readline meh >/dev/null; }; foo; unset foo"
        )

    def test_github_issue_189_1(self, bash):
        """Test error messages on a certain command line

        Reported at https://github.com/scop/bash-completion/issues/189

        Syntax error messages should not be shown by completion on the
        following line:
        
          $ ls -- '${[TAB]
          $ rm -- '${[TAB]
        
        """
        assert_bash_exec(bash, "quote_readline $'\\'${' >/dev/null")

    def test_github_issue_492_1(self, bash):
        """Test unintended code execution on a certain command line

        Reported at https://github.com/scop/bash-completion/pull/492

        Arbitrary commands could be unintendedly executed by 
        _quote_readline_by_ref.  In the following example, the command 
        "touch 1.txt" would be unintendedly created before the fix.  The file
        "1.txt" should not be created by completion on the following line:
        
          $ echo '$(touch file.txt)[TAB]

        """
        assert_bash_exec(bash, "quote_readline $'\\'$(touch 1.txt)' >/dev/null")
        assert not os.path.exists("./1.txt")

    def test_github_issue_492_2(self, bash):
        """Test the file clear by unintended redirection on a certain command line

        Reported at https://github.com/scop/bash-completion/pull/492

        The file "1.0" should not be created by completion on the following
        line:
        
          $ awk '$1 > 1.0[TAB]
        
        """
        assert_bash_exec(bash, "quote_readline $'\\'$1 > 1.0' >/dev/null")
        assert not os.path.exists("./1.0")

    def test_github_issue_492_3(self, bash):
        """Test code execution through unintended pathname expansions

        When there is a file named "quote=$(COMMAND)" (for _filedir) or
        "ret=$(COMMAND)" (for quote_readline), the completion of the word '$*
        results in the execution of COMMAND.
        
          $ echo '$*[TAB]
    
        """
        os.mkdir("./ret=$(echo injected >&2)")
        assert_bash_exec(bash, "quote_readline $'\\'$*' >/dev/null")

@pytest.mark.bashcomp(cmd=None, temp_cwd=True, pre_cmds=("shopt -s failglob",))
class TestUnitQuoteReadlineWithFailglob:

    def test_github_issue_492_4(self, bash):
        """Test error messages through unintended pathname expansions

        When "shopt -s failglob" is set by the user, the completion of the word
        containing glob character and special characters (e.g. TAB) results in
        the failure of pathname expansions.
        
          $ shopt -s failglob
          $ echo a\\	b*[TAB]
        
        """
        assert_bash_exec(bash, "quote_readline $'a\\\\\\tb*' >/dev/null")
