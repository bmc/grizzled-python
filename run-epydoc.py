import os

# Run this from the top-level directory.

EPYDOC_ARGS = ['-c', 'epydoc.cfg', 'grizzled', '-o', 'epydoc']

if __name__ == '__main__':
    os.system(' '.join(['epydoc'] + EPYDOC_ARGS))
