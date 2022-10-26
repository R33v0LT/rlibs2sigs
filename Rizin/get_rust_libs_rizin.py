import re
import rzpipe

import libs2sigs

binary_path = './lib.so'
pattern = re.compile(r'([\w\d\-_]+)-(\d+\.\d+\.\d+)')

rz = rzpipe.open(binary_path)
rz.cmd('aa')

libs = set(re.findall(pattern, rz.cmd('izQ')))

print('Found %d libraries!' % len(libs))

for lib, version in libs:
    print('%s = "%s"' % (lib, version))

libs2sigs.rlib_to_sig(libs, 'rizin')