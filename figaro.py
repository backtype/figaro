import os
import sys
import yaml
from mako.template import Template, exceptions

FIGARO_FILE = "FIGARO"
FIGARO_SUFFIX = ".figaro"
DEFAULT_MODE = "default"
ASSETS_FILE = "assets.yml"
CONFIG = "_config"

#get mode from the command line: i.e., python figaro.py local
#walk directory tree and find all FIGARO files
#for each FIGARO file, read in the "config" name from the file (or even multiple names)
#for each config, read in global assets.yml and local assets.yml to create a dict. also set "__MODE__" to the passed in mode
#run templating from template (all .figaro files) to config/{file without .figaro}

#get the stripped lines out of the file that aren't all whitespace
def get_substance_lines(file_path):
    f = open(file_path, "r")
    lines = f.readlines()
    f.close()
    return filter(lambda x: len(x) > 0, map(lambda x: x.strip(), lines))

#get all dirs along path
def get_all_dirs(full_path, base_path):
    path = full_path[len(base_path):].lstrip("/")
    dirs = [base_path]
    while True:
        parts = path.split("/", 1)
        if parts[0] != "":
            path = path[len(parts[0])+1:]
            dirs.append(parts[0])
            yield os.path.join(*dirs)
        else:
            return

CONFIG_CACHE = {}
def load_file(file_path):
    try:
        return CONFIG_CACHE[file_path]
    except:
        config = yaml.load(file(file_path, "r"))
        CONFIG_CACHE[file_path] = config
        return config

def read_assets_into_dict(file_path, mode, adict):
    #second condition is a hack b/c yaml was giving errors for empty files on mike's machine
    if not os.path.exists(file_path) or len(get_substance_lines(file_path)) == 0:
        return
    config = load_file(file_path)
    if config != None:
        for k, v in config.items():
            if mode in v:
                adict[k] = v[mode]
            elif DEFAULT_MODE in v:
                adict[k] = v[DEFAULT_MODE]


def run_template(template_file, target_dir, assets):
    fname = os.path.split(template_file)[1]
    fname = fname[:len(fname)-len(FIGARO_SUFFIX)]
    target_file = target_dir + "/" + CONFIG + "/" + fname
    if not os.path.exists(target_dir + "/" + CONFIG):
        os.mkdir(target_dir + "/" + CONFIG)
    template = Template(filename=template_file)
    f = open(target_file, "w")
    try:
        f.write(template.render(**assets) + "\n")
    except:
        print exceptions.html_error_template().render()
        raise
    finally:
        f.close()

def run_choice(target_dir, figaro_root, mode, choice, override_assets):
    choice_dir = figaro_root + "/" + choice
    assets = {}
    read_assets_into_dict(figaro_root + "/" + ASSETS_FILE, mode, assets)
    for dir_ in get_all_dirs(choice_dir, figaro_root):
        if dir_:
            read_assets_into_dict(dir_ + "/" + ASSETS_FILE, mode, assets)
    for f in override_assets:
        read_assets_into_dict(figaro_root + "/" + f, mode, assets)
    assets["__mode__"] = mode
    templates = filter(lambda f: f.endswith(FIGARO_SUFFIX), os.listdir(choice_dir))
    for template in templates:
        run_template(choice_dir + "/" + template, target_dir, assets)
    
def run_figaro(mode, figaro_root, walk_root, override_assets):
    walk = os.walk(walk_root)

    for dir_info in walk:
        #(dirpath, dirnames, filenames)
        if FIGARO_FILE in dir_info[2]:
            choices = get_substance_lines(dir_info[0] + "/" + FIGARO_FILE)
            for choice in choices:
                run_choice(dir_info[0], figaro_root, mode, choice, override_assets)
    
def main():
    if len(sys.argv) < 3:
        print "Usage: python figaro.py [figaro_root] [mode] [walk_root]=. [override_assets]"
        print "override_assets -- optional list of .yml files relative to figaro_root"
        sys.exit()
    figaro_root = sys.argv[1]
    mode = sys.argv[2]
    if mode == DEFAULT_MODE:
        raise RuntimeError("Cannot set mode to " + DEFAULT_MODE)
    walk_root = "."
    override_assets = []
    if len(sys.argv) > 3:
        if not sys.argv[3].endswith(".yml"):
            walk_root = sys.argv[3]
        for i in range(3, len(sys.argv)):
            if sys.argv[i].endswith(".yml"):
                override_assets.append(sys.argv[i])
    run_figaro(mode, figaro_root, walk_root, override_assets)
                
if __name__ == "__main__":
    main()
