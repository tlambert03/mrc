=====
mrc
=====

.. image:: https://img.shields.io/pypi/v/mrc.svg
        :target: https://pypi.python.org/pypi/mrc

.. image:: https://travis-ci.com/tlambert03/mrc.svg?branch=master
        :target: https://travis-ci.com/tlambert03/mrc


Read and write .mrc and .dv (deltavision) image file format

Note, this module is designed to read the MRC variant used by
deltavision microscopes (.dv). For the MRC file format frequently
used for structural biology, see https://github.com/ccpem/mrcfile

(thought dv and mrc formats are very similar, dv files have a slightly
different header, and lack the character string "MAP" in bytes 209-212
in the `header <http://www.ccpem.ac.uk/mrc_format/mrc2014.php>`_, preventing mrcfile from working).


Credits
-------

This package was created by Sebastian Haase as a part of the
`priithon <https://github.com/sebhaase/priithon/blob/master/Priithon/Mrc.py>`_ package.  It is mostly just repackaged here and updated
for python 3.
