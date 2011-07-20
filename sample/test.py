import os

# run: "nosetests ."

def test_figaro():
    os.system("sh figaro prod")
    assert open("proj/_config/config.py").read() == "FOO = \"foo\"\n\nBAR = \"bar-prod\"\n"
    os.system("rm -rf proj/_config")