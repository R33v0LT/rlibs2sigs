import configparser
import os
import re
import subprocess
import textwrap

import requests
from bs4 import BeautifulSoup
from rust_demangler import demangle

EXTERNS = set()
EXAMPLE_FUNCS = list()
LIB_FUNCS = list()
USINGS = dict()
RUST_PROJ_NAME = ''
RUST_PROJ_PATH = ''
PAT_GENERATOR_PATH = ''
SIGMAKE_PATH = ''
ARCH = ''

VARIABLES = {'bool': 'boolean',
             'u8': 'ubyte', 'u16': 'uword', 'u32': 'udword', 'u64': 'uqword',
             'i8': 'byte', 'i16': 'word', 'i32': 'dword', 'i64': 'qword',
             'f32': 'float', 'f64': 'double',
             'char': 'character', '&str': 'string1', 'String': 'string2',
             '&[u8]': 'ref_arr_u8', '&[u16]': 'ref_arr_u16',
             '&[u32]': 'ref_arr_u32', '&[u64]': 'ref_arr_u64',
             '&[i8]': 'ref_arr_i8', '&[i16]': 'ref_arr_i16',
             '&[i32]': 'ref_arr_i32', '&[i64]': 'ref_arr_i64',
             '&mut [u8]': 'mut_u8', '&mut [u16]': 'mut_u16',
             '&mut [u32]': 'mut_u32', '&mut [u64]': 'mut_u64',
             '&mut [i8]': 'mut_i8', '&mut [i16]': 'mut_i16',
             '&mut [i32]': 'mut_i32', '&mut [i64]': 'mut_i64',
             '&mut str': 'mut_str', '&mut String': 'mut_str2', '&char': 'mut_char',
             'usize': 'arch_uint', 'isize': 'arch_int',
             '&usize': 'arch_ref_uint', '&isize': 'arch_ref_int',
             '&mut usize': 'arch_ref_mut_uint', '&mut isize': 'arch_ref_mut_int'}

DEFINES = (
    'let mut mut_str = String::from("123").as_mut();',
    'let mut mut_str2 = &mut String::from("123");',
    'let boolean = true;',
    'let ubyte = 1u8;',
    'let uword = 1u16;',
    'let udword = 1u32;',
    'let uqword = 1u64;',
    'let byte = 1i8;',
    'let word = 1i16;',
    'let dword = 1i32;',
    'let qword = 1i64;',
    'let float = 1f32;',
    'let double = 1f64;',
    "let character = '1';",
    'let string1 = "123";',
    'let string2 = String::from("123");',
    'let ref_arr_u8 = &[1u8, 2u8];',
    'let ref_arr_u16 = &[1u16, 2u16];',
    'let ref_arr_u32 = &[1u32, 2u32];',
    'let ref_arr_u64 = &[1u64, 2u64];',
    'let ref_arr_i8 = &[1i8, 2i8];',
    'let ref_arr_i16 = &[1i16, 2i16];',
    'let ref_arr_i32 = &[1i32, 2i32];',
    'let ref_arr_i64 = &[1i64, 2i64];',
    'let mut mut_u8 = &mut [1u8, 2u8];',
    'let mut mut_u16 = &mut [1u16, 2u16];',
    'let mut mut_u32 = &mut [1u32, 2u32];',
    'let mut mut_u64 = &mut [1u64, 2u64];',
    'let mut mut_i8 = &mut [1i8, 2i8];',
    'let mut mut_i16 = &mut [1i16, 2i16];',
    'let mut mut_i32 = &mut [1i32, 2i32];',
    'let mut mut_i64 = &mut [1i64, 2i64];',
    "let mut mut_char = 'b';",
    'let arch_uint: usize = 8;',
    'let arch_int: isize = 8;',
    'let arch_ref_uint: &usize = &8;',
    'let arch_ref_int: &isize = &8;',
    'let mut arch_ref_mut_uint: &mut usize = &mut 8;',
    'let mut arch_ref_mut_int: &mut isize = &mut 8;',
)


def get_lib_funcs(lib, ver):
    '''Get all functions html path'''

    url = 'https://docs.rs/{}/{}'

    r = requests.get(url.format(lib, ver) + '/#functions')

    soup = BeautifulSoup(r.text, 'html.parser')

    result = []
    for link in soup.find_all('a', attrs={'class': 'fn'}):
        result.append(link.get('href'))

    return result


def get_lib_funcs_code(funcs, lib, ver):
    '''Get all fuctions code from html page'''

    full_code = []

    for func in funcs:
        func_code = get_func_code(lib, ver, func)

        if func_code:
            new_code = update_func(lib, func_code, func)
            full_code.append(new_code)

    if len(full_code) == 0:
        func_code = get_func_code(lib, ver)
        if func_code:
            new_code = update_func(lib, func_code, 'fn.main.html')
            full_code.append(new_code)

    return full_code


def update_func(lib, func_code, func):
    '''Change some function code to be called later in lib.rs'''

    for i, code in enumerate(func_code):
        replace_name = f'{lib.replace("-", "_")}_{func[3:-5]}_example_{i}'
        EXAMPLE_FUNCS.append(replace_name)

        code = code.replace('Box<Error>', 'Box<dyn Error>') \
            .replace('struct', 'pub struct') \
            .replace(';Run', ';')

        if 'main' in code:
            code = code.replace('fn main', f'pub fn {replace_name}')

            return strip_externs(code)

        func_name = re.search(r'^fn ([\w\d_]+\()', code, re.MULTILINE)
        pub_func_name = re.search(r'^pub fn ([\w\d_]+\()', code, re.MULTILINE)

        if pub_func_name:
            code = code.replace(
                pub_func_name.group(1), f'{replace_name}(')

        elif func_name:
            code = code.replace(
                func_name.group(0), f'pub fn {replace_name}(')

        else:
            code = f'pub fn {replace_name}() {{\n' + code + '\n}'

        return strip_externs(code)


def get_func_code(lib: str, ver: str, func=''):
    '''Get single function code from it's html page'''

    url = f'https://docs.rs/{lib}/{ver}/{lib.replace("-", "_")}/{func}'

    soup, examples = get_example(url)

    check_template(soup, lib)

    if examples:
        return map(lambda x: x.text, examples)


    return None

def get_example(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')

    examples = soup.find_all(
        'pre', attrs={'class': 'rust rust-example-rendered'})

    return soup, examples

def check_template(soup: BeautifulSoup, lib):
    fn_template = soup.find_all('pre', attrs={'class': 'rust fn'})

    fn_regex = re.compile(r'([\w\d]|>)\((.*)\)( ->|\n|$)')
    type_regex = re.compile(r': ([&\[\]\w\d \'<>]+)')
    fn_name_regex = re.compile(r'fn ([\w\d_]+)|([\w\d_])+<.*>\(')
    fn_name = str()
    types = list()

    for tmpl in fn_template:
        args = re.search(fn_regex, tmpl.text)
        fn_name = re.search(fn_name_regex, tmpl.text).group(1)

        if fn_name == '':
            return False

        if args.group(2):
            types = re.findall(type_regex, args.group(2))
        else:
            types = []

    args = []
    for t in types:
        lifetime = re.findall(r'\'\w+ ', t)
        if lifetime:
            t = t.replace(lifetime[0], '')

        if t in VARIABLES.keys():
            args.append(VARIABLES[t])
        else:
            print(f'Unexpected type: {t}')
            return False

    if fn_name != '':
        LIB_FUNCS.append(f"{lib.replace('-', '_')}::{fn_name}({', '.join(args)});")
        USINGS[lib].append(fn_name)

    return True


def strip_externs(code):
    '''Strip externs from modules and save them for use in lib.rs'''

    lines = code.split('\n')

    for line in code.split('\n'):
        if 'extern' in line:
            crate = re.search(r'extern crate (.*);',
                              lines.pop(lines.index(line)))

            EXTERNS.add(crate.group(1))

        elif '#[macro_use]' in line:
            lines.pop(lines.index(line))

    return '\n'.join(lines)


def check_compile():
    '''Check every function for compilation. If succeed, add it to lib.rs'''

    head = '#![allow(unused_imports)]\n#![allow(dead_code)]\n\n'
    head += '\n'.join(map(lambda x: f'#[macro_use]\nextern crate {x.replace("-", "_")};\n',
                          set(EXTERNS)))
    head += '\n'

    mods = ''
    candidates = ''
    usings = ''
    variables = ''

    for define in DEFINES:
        variables += f'        {define}\n'

    for i in range(len(LIB_FUNCS)):
        candidate = f'        {LIB_FUNCS[i]}\n'

        full_code = head + '\npub mod smth {\n' + \
            '\n    #[no_mangle]\n    pub extern "C" fn main() {\n' + \
            variables + candidate + '    }\n' + '}'

        if cargo_check(full_code, LIB_FUNCS[i]):
            candidates += candidate

    for i in range(len(EXAMPLE_FUNCS)):
        mod = f'mod func{i};\n'
        candidate = f'        {EXAMPLE_FUNCS[i]}();\n'
        use = f'    use crate::func{i}::{EXAMPLE_FUNCS[i]};\n'

        full_code = head + mod + '\npub mod smth {\n' + use + \
            '\n    #[no_mangle]\n    pub extern "C" fn main() {\n' + \
            variables + candidate + '    }\n' + '}'

        if cargo_check(full_code, EXAMPLE_FUNCS[i]):
            candidates += candidate
            mods += mod
            usings += use

    lib_code = head + mods + '\npub mod smth {\n' + usings + \
        '\n    #[no_mangle]\n    pub extern "C" fn main() {\n' + \
        variables + candidates + '    }\n' + '}'

    with open(f'{RUST_PROJ_PATH}/{RUST_PROJ_NAME}/src/lib.rs', 'w') as rust_lib:
        rust_lib.write(lib_code)


def cargo_check(code, func):

    with open(f'{RUST_PROJ_PATH}/{RUST_PROJ_NAME}/src/lib.rs', 'w') as rust_lib:
        rust_lib.write(code)

    if ARCH:
        proc = subprocess.run(['cargo', 'check', '--release',
                            f'--manifest-path={RUST_PROJ_PATH}/{RUST_PROJ_NAME}/Cargo.toml',
                            f'--target={ARCH}'],
                            capture_output=True)
    else:
        proc = subprocess.run(['cargo', 'check', '--release',
                            f'--manifest-path={RUST_PROJ_PATH}/{RUST_PROJ_NAME}/Cargo.toml'],
                            capture_output=True)        

    if b'error[' in proc.stderr or b'error: could not compile' in proc.stderr:
        print(f'Error on compile function: {func}. Removing it!')
        return False

    return True


def create_mods(mods):
    '''Create modules from each example function codes'''

    for i in range(len(mods)):
        with open(f'{RUST_PROJ_PATH}/{RUST_PROJ_NAME}/src/func{i}.rs', 'wb') as code:
            code.write(mods[i].encode(errors='replace'))


def cargo_build():
    '''Compile code with cargo'''

    if ARCH:
        os.system('cargo build --release '
                f'--manifest-path={RUST_PROJ_PATH}/{RUST_PROJ_NAME}/Cargo.toml '
                f'--target={ARCH}')
    else:
        os.system('cargo build --release '
                f'--manifest-path={RUST_PROJ_PATH}/{RUST_PROJ_NAME}/Cargo.toml')


def get_latest_version(lib):
    '''Get the latest version of specified library'''

    url = f'https://docs.rs/{lib}/latest/{lib}/'
    r = requests.get(url)

    soup = BeautifulSoup(r.text, 'html.parser')

    li_ver = soup.find('li', attrs={'class': 'version'})
    if li_ver == None:
        div_ver = soup.find('div', attrs={'class': 'version'}).text[8:]
        return div_ver

    return li_ver.text[8:]


def gen_cargo_toml(libs):
    '''Generate valid Cargo.toml'''

    cargo_template = textwrap.dedent(
        '''
        [package]
        name = "rust_codes"
        version = "0.1.0"
        edition = "2021"

        [profile.release]
        debug = true
        strip = false

        [lib]
        crate-type = ["staticlib", "cdylib"]

        [dependencies]
        %s
        ''')

    toml_path = f'{RUST_PROJ_PATH}/{RUST_PROJ_NAME}/Cargo.toml'

    deps = ''
    for lib, version in libs:
        deps += '%s = "%s"\n' % (lib, version)

    for ext in EXTERNS:
        if not f'{ext} =' in deps and not f'{ext.replace("_", "-")} =' in deps:
            version = get_latest_version(ext)

            deps += '%s = "%s"\n' % (ext, version)

    with open(toml_path, 'w') as toml:
        toml.write(cargo_template % deps)


def cargo_new():
    if os.path.isdir(f'{RUST_PROJ_PATH}/{RUST_PROJ_NAME}'):
        return

    os.chdir(RUST_PROJ_PATH)
    os.system(f'cargo new {RUST_PROJ_NAME} --lib --vcs none')


def create_sig_ida():
    target = f'{RUST_PROJ_PATH}/{RUST_PROJ_NAME}/target/{ARCH}/release'

    if os.name == 'nt':
        libname = f'{RUST_PROJ_NAME}.lib'
    else:
        libname = f'lib{RUST_PROJ_NAME}.a'

    os.system(f'{PAT_GENERATOR_PATH} {target}/{libname} {target}/{libname}.pat')

    rust_demangle(f'{target}/{libname}.pat')

    cmd = f'{SIGMAKE_PATH} {target}/{libname}.pat {target}/{libname}.sig'
    proc = subprocess.run(cmd.split(), capture_output=True)

    if b'COLLISIONS' in proc.stderr:
        exc = open(f'{target}/{libname}.exc').readlines()[4:]

        with open(f'{target}/{libname}.exc', 'w') as sigexc:
            sigexc.write('\n'.join(exc))
            subprocess.run(cmd.split())

def create_sig_rizin():
    target = f'{RUST_PROJ_PATH}/{RUST_PROJ_NAME}/target/{ARCH}/release'

    if os.name == 'nt':
        libname = f'{RUST_PROJ_NAME}.dll'
    else:
        libname = f'lib{RUST_PROJ_NAME}.so'

    # cmd = f'rz-sign -a -o {target}/{libname}.sig {target}/{libname}'
    cmd = f'rizin -A -qc "zfc {target}/{libname}.sig" {target}/{libname}'
    os.system(cmd)

def rust_demangle(target):
    mangled_regex = re.compile(r'_ZN[\w\d_$\.]+E'.encode())

    with open(target, 'rb') as mangled_file:
        mangled_content = mangled_file.read()
        mangled_names = re.findall(mangled_regex, mangled_content)

        for name in mangled_names:
            mangled_content = mangled_content.replace(
                name, demangle(name.decode()).encode().replace(b' ', b''))

    with open(target, 'wb') as demangled_file:
        demangled_file.write(mangled_content)

def parse_config(conf_path):
    config = configparser.ConfigParser()
    config.read(conf_path)

    global RUST_PROJ_NAME
    global RUST_PROJ_PATH
    global PAT_GENERATOR_PATH
    global SIGMAKE_PATH
    global ARCH

    RUST_PROJ_NAME = config['Project']['name']
    RUST_PROJ_PATH = config['Project']['path']
    
    try:
        PAT_GENERATOR_PATH = config['Generator']['pat']
        SIGMAKE_PATH = config['Generator']['sigmake']

    except:
        pass

    ARCH = config['Target']['arch']

def rlib_to_sig(libs, target='ida'):
    parse_config(r'E:\DSEC\rust\rlibs2sigs\config.ini')

    all_funcs = list()
    all_modules = list()

    for lib, ver in libs:
        USINGS[lib] = []    
        EXTERNS.add(lib.replace('-', '_'))

        lib_funcs = get_lib_funcs(lib, ver)
        all_modules.extend(get_lib_funcs_code(lib_funcs, lib, ver))
        all_funcs.extend(lib_funcs)

    cargo_new()

    gen_cargo_toml(libs)

    create_mods(all_modules)
    check_compile()

    cargo_build()

    if target == 'ida':
        create_sig_ida()

    elif target == 'rizin':
        create_sig_rizin()


# if __name__ == '__main__':
#     libs = set([('cesu8', '1.1.0'), ('memchr', '2.4.1'), ('proc-maps', '0.2.0'), ('log', '0.4.1'), ('lazy_static', '1.4.0'), ('rustc-demangle', '0.1.2'),
#                 ('serde_json', '1.0.7'), ('aho-corasick', '0.7.1'), ('regex', '1.5.4'), ('regex-syntax', '0.6.2'), ('miniz_oxide', '0.4.0'), ('rand', '0.8.4')])

#     rlib_to_sig(libs)
